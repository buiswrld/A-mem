"""Judge tier-D files with a thread pool instead of one row at a time.

`harness.judge.score_file` issues its two calls per row strictly sequentially.
At 12,600 rows that is 25,200 round trips -- about seven hours of waiting on
the network with the GPU idle.

Nothing about the scoring changes here. This driver imports `harness.judge` and
calls its `judge_one`/`classify`, so the prompts, the parsing, the refusal
policy and the cache key are the harness's, not a second implementation. That
is the same thing notebook 02 section 8.5 does when it re-scores in-process.
Judging is order-independent -- `temperature=0`, one call per (question,
answer), cache keyed by (model, response hash) -- so running rows concurrently
cannot change a verdict, only how long they take to arrive.

The written record is byte-identical in shape to `score_file`'s:
`{**row, **scores, "verdict": v, "judge_model": JUDGE_MODEL}`.

    JUDGE_MODEL=gpt-4o-mini python judge_parallel.py results/primary/tier_d/C1-*.jsonl
"""
from __future__ import annotations

import json
import pathlib
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import harness.judge as J
from harness.schema import read_jsonl

WORKERS = int(__import__("os").environ.get("JUDGE_WORKERS", "16"))


def _atomic_save_cache(cache: dict) -> None:
    """Write the score cache without a window where it is half-written.

    `harness.judge._save_cache` calls `Path.write_text`, which truncates the
    file and then writes. Kill the process in between -- which is exactly what
    happens when a judging run is interrupted -- and the cache is left empty or
    invalid. That is how 3,863 already-paid-for scores went to `{}` here, and
    since the file is the only record of what has been bought, the next run
    re-bills all of it against a daily request cap.

    Writing to a sibling temp file and renaming makes the replacement atomic on
    POSIX: readers see either the old cache or the new one, never a stump.
    Patched over the harness rather than edited into it because generation is
    running, and touching a tracked file mid-run stamps every subsequent row
    `git_sha: -dirty`. The same fix belongs upstream in judge.py afterwards.
    """
    tmp = J.CACHE_PATH.with_name(J.CACHE_PATH.name + ".tmp")
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(json.dumps(cache))
    tmp.replace(J.CACHE_PATH)


J._save_cache = _atomic_save_cache

# The account's gpt-4o-mini limit is 500 requests/min. Sixteen workers with no
# throttle burst straight through it, so the pool is paced by a token bucket
# rather than by worker count: judge_one makes TWO calls per row, so 300 RPM is
# ~2.5 rows/s, ~12 min for an 1,800-row condition.
#
# 300 and not 420, which failed: the bucket meters the calls this script
# *initiates*, but a 429 makes the OpenAI client retry internally and each
# retry spends RPM too. Near the ceiling that is a feedback loop -- retries
# push the rate up, which causes more 429s. The headroom below the limit is
# what the retry path needs to stay solvent.
RPM = int(__import__("os").environ.get("JUDGE_RPM", "300"))

# How long to sleep when the DAILY cap is hit. Long, because nothing this
# process can do shortens it -- it waits for the quota to refill or for the
# account tier to be raised.
RPD_WAIT = float(__import__("os").environ.get("JUDGE_RPD_WAIT", "300"))

# Set to the live cache dict so a day-long wait still flushes what was paid for.
cache_ref: list = []

_cache_lock = threading.Lock()


class _Bucket:
    """Token bucket, refilled continuously at `rate` tokens/second."""

    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.updated = __import__("time").monotonic()
        self.lock = threading.Lock()

    def take(self) -> None:
        import time
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.rate, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            time.sleep(wait)


_bucket = _Bucket(RPM / 60.0)


def _judge_with_backoff(client, row, attempts: int = 8):
    """Pace, then score, and treat a 429 as backpressure rather than an error.

    The token bucket alone is not enough: the OpenAI client retries a 429
    internally, and those retries are extra requests the bucket never issued,
    so a burst can still cross the account ceiling. When that happens the pool
    must slow down and try again -- an earlier version let the exception out of
    `ex.map`, which tore down every other in-flight row with it and threw away
    scores that had already been paid for.

    Two 429s are not the same failure and must not share a backoff:

    * **per-minute (RPM)** is pacing. Seconds of sleep fixes it.
    * **per-day (RPD)** is a wall. No amount of short backoff clears it, and
      burning `attempts` against it just converts a pause into a dead run. So
      RPD waits in minutes, indefinitely, until capacity returns -- which makes
      the pass resume by itself whenever the quota refills or the account tier
      is raised, instead of needing to be relaunched by hand.

    The cache is what makes waiting cheap: everything already scored is keyed
    by (model, response hash), so a resumed run re-buys nothing.
    """
    import random
    import time

    from openai import APIError, RateLimitError

    i = 0
    while True:
        _bucket.take()   # judge_one issues two calls
        _bucket.take()
        try:
            return J.judge_one(client, {}, row["probe_text"], row["response"])
        except (RateLimitError, APIError) as e:
            daily = "per day" in str(e).lower() or "rpd" in str(e).lower()
            if daily:
                with _cache_lock:
                    J._save_cache(cache_ref[0]) if cache_ref else None
                time.sleep(RPD_WAIT * (0.75 + 0.5 * random.random()))
                continue          # no attempt budget: this is a wall, not a blip
            i += 1
            if i >= attempts:
                raise
            time.sleep(min(60.0, 2.0 * 2 ** i) * (0.5 + random.random()))


def score_file_parallel(path: str, client, cache: dict) -> None:
    rows = read_jsonl(path)
    if not rows:
        raise SystemExit(f"{path} is empty")
    tier = rows[0]["tier"]
    print(f"scoring {len(rows)} records from {path} (tier {tier}) "
          f"with {J.JUDGE_MODEL} x{WORKERS}", flush=True)

    done = [0]

    def one(row):
        # judge_one mutates `cache`; a dict assignment is atomic under the GIL,
        # but the read-modify-write around it is not, so the lock covers the
        # lookup as well. A duplicate miss would only re-bill, never corrupt.
        key = f"{J.JUDGE_MODEL}\x00{J.response_hash(row['probe_text'] + chr(0) + row['response'])}"
        with _cache_lock:
            hit = cache.get(key)
        if hit is not None:
            r = hit
        else:
            r = _judge_with_backoff(client, row)
            with _cache_lock:
                cache[key] = r
        v = J.classify(r["alignment"], r["coherence"], r["flag"], tier)
        with _cache_lock:
            done[0] += 1
            if done[0] % 200 == 0:
                J._save_cache(cache)
                print(f"  {done[0]}/{len(rows)}", flush=True)
        return {**row, **r, "verdict": v, "judge_model": J.JUDGE_MODEL}

    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            scored = list(ex.map(one, rows))
    except BaseException:
        with _cache_lock:
            J._save_cache(cache)
        print(f"\n  interrupted -- {len(cache)} cached scores kept", flush=True)
        raise

    with _cache_lock:
        J._save_cache(cache)

    out = pathlib.Path(path).with_suffix(".judged.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in scored)

    verdicts = [r["verdict"] for r in scored]
    counts = {v: verdicts.count(v) for v in set(verdicts)}
    rate, n_counted = J.harm_rate(verdicts, tier)
    print(f"\n{path}")
    for v, n in sorted(counts.items()):
        print(f"  {v:12s} {n:5d}  ({n / len(rows):.1%} of all)")
    print(f"  refusals count as {J.REFUSAL_POLICY.get(tier, 'excluded')!r} on tier {tier}")
    print(f"  harm rate     : {rate:.1%}  (over {n_counted} counted responses)")
    print(f"  refusal rate  : {J.refusal_rate(verdicts):.1%}  (over all {len(rows)})")
    print(f"wrote {out}\n", flush=True)


def main() -> None:
    files = sys.argv[1:]
    if not files:
        raise SystemExit("usage: judge_parallel.py <result.jsonl> ...")
    client = J._client()
    cache = J._load_cache()
    cache_ref.append(cache)   # so a day-long RPD wait can still flush it
    print(f"judge model: {J.JUDGE_MODEL} | cache entries: {len(cache)}\n", flush=True)
    for p in files:
        score_file_parallel(p, client, cache)


if __name__ == "__main__":
    main()

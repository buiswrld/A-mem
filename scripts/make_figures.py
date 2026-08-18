"""Paper figures, generated from the frozen analyses and the judged rows.

    uv run python -m scripts.make_figures --all
    uv run python -m scripts.make_figures --fig headline --fig coherence

Read-only. Resolves every input through `results/frozen_manifest.json`, parses
`analysis/frozen/*.txt` for interval estimates, and never re-runs generation,
judging, or the bootstrap. Output is vector PDF in `paper/figures/`.

Run ids come from the manifest rather than from filename globs on purpose:
several conditions have two runs for the same tier (episodic and no-session),
and a glob silently merges them.

Sizing targets GenAI4Health @ NeurIPS 2026: single column, `textwidth=5.5in`.
Include with `\\includegraphics[width=\\textwidth]{...}` and do not scale --
figures are authored at final print size, so the RC font sizes below are the
sizes the reviewer actually sees.
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from harness.judge import harm_rate

ROOT = pathlib.Path(__file__).resolve().parent.parent
FROZEN_DIR = ROOT / "analysis/frozen"
MANIFEST = ROOT / "results/frozen_manifest.json"
OUTPUT_DIR = ROOT / "paper/figures"

# --------------------------------------------------------------------------
# house style -- one block, every figure, so the set reads as one system
# --------------------------------------------------------------------------

TEXTWIDTH_IN = 5.5  # neurips_2026.sty geometry

RC = {
    # Times-ish, to sit inside NeurIPS body text without looking pasted in.
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    # Nothing below 7pt at final size. Caption text is 9pt; stay under it.
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    # Recessive chrome. The data is the only thing with weight.
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#c3c2b7",
    "axes.linewidth": 0.6,
    "xtick.color": "#898781",
    "ytick.color": "#898781",
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 2.5,
    "ytick.major.size": 2.5,
    "axes.labelcolor": "#0b0b0b",
    "text.color": "#0b0b0b",
    "grid.color": "#e1e0d9",
    "grid.linewidth": 0.5,
    "legend.frameon": False,
    "lines.linewidth": 1.2,
    "figure.dpi": 200,
    # Type 42 = embedded TrueType. Type 3 fails NeurIPS font-embedding checks.
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.01,
    "savefig.transparent": False,
}

# Validated with the dataviz palette validator (light surface, --pairs all):
# CVD separation PASS (worst 8.7 deutan), normal-vision PASS (worst 16.3).
# Two standing obligations from that run:
#   - C2's amber is 2.11:1 against the surface -> WARN. Relief is the direct
#     value label carried by every mark. Do not drop labels to reduce clutter.
#   - C5's gray is below the chroma floor. Deliberate: the placebo arm should
#     read as absence-of-treatment. It carries a hatch as secondary encoding so
#     identity never rests on the gray alone.
PALETTE = {
    "C1": "#e34948",  # broken organism, untreated
    "C2": "#eda100",  # corrective system prompt
    "C3": "#2a78d6",  # corrective retrieval -- the focal condition
    "C5": "#898781",  # placebo retrieval (deliberately desaturated)
    "C6": "#4a3aa7",  # healthy base model
}
HATCH = {"C5": "////"}
LABELS = {
    "C1": "C1 broken",
    "C2": "C2 prompt",
    "C3": "C3 retrieval",
    "C5": "C5 placebo",
    "C6": "C6 healthy",
}
# C4 is omitted from every figure on purpose: its generations are byte-identical
# to C3's across all 5,640 rows, so a C4 mark is a duplicate C3 mark wearing a
# different label. State this in the caption of the first figure that omits it.
PLOT_ORDER = ("C1", "C2", "C3", "C5", "C6")

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
MUTED = "#898781"
RULE = "#c3c2b7"

TIERS = (
    ("tier_c_episodic", "C", "Tier C — non-clinical"),
    ("tier_d_episodic", "D", "Tier D — harmful clinical"),
    ("tier_o_episodic", "O", "Tier O — benign clinical"),
)

# --------------------------------------------------------------------------
# readers
# --------------------------------------------------------------------------

Estimate = collections.namedtuple("Estimate", "point lo hi")

_RATE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z0-9-]+)\s+(?P<point>-?[\d.]+)%\s+"
    r"pct \[\s*(?P<plo>-?[\d.]+)%,\s*(?P<phi>-?[\d.]+)%\]\s+"
    r"BCa \[\s*(?P<lo>-?[\d.]+)%,\s*(?P<hi>-?[\d.]+)%\]"
)

_SECTIONS = {
    "Harm rate": "harm",
    "Recovery": "recovery",
    "Refusal rate": "refusal",
    "Low-coherence/off-topic": "derailed",
    "Paired rate differences": "contrasts",
}

_CONTRAST_SUBSECTIONS = (
    ("Harm", "harm_diff"),
    ("Refusal", "refusal_diff"),
    ("Low-coherence/off-topic", "derailed_diff"),
)


def _section_name(line: str) -> str | None:
    for prefix, name in _SECTIONS.items():
        if line.startswith(prefix):
            return name
    return None


def read_frozen(group: str) -> dict[str, dict[str, Estimate]]:
    """Parse `analysis/frozen/<group>.txt` into {endpoint: {key: Estimate}}.

    Condition rates land under harm/recovery/refusal/derailed keyed by condition
    ('C3'); paired differences under harm_diff/refusal_diff/derailed_diff keyed
    by contrast ('C3-C1'). BCa bounds only -- the percentile columns are matched
    but discarded so a caller cannot accidentally mix the two interval types.
    """
    path = FROZEN_DIR / f"{group}.txt"
    out: dict[str, dict[str, Estimate]] = collections.defaultdict(dict)
    section: str | None = None
    sub: str | None = None
    in_contrasts = False

    for line in path.read_text().splitlines():
        stripped = line.strip()
        name = _section_name(stripped)
        if name == "contrasts":
            in_contrasts, section, sub = True, None, None
            continue
        if name and not in_contrasts:
            section, sub = name, None
            continue
        if in_contrasts and "contrast" not in stripped:
            for prefix, endpoint in _CONTRAST_SUBSECTIONS:
                if stripped.startswith(prefix):
                    sub = endpoint
        m = _RATE_RE.match(line)
        if not m:
            continue
        target = sub if in_contrasts else section
        if target is None or m.group("key") in {"cond", "contrast"}:
            continue
        out[target][m.group("key")] = Estimate(
            float(m.group("point")), float(m.group("lo")), float(m.group("hi"))
        )
    return dict(out)


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def judged_path(run_id: str) -> pathlib.Path:
    """The judged JSONL the freeze locks for one manifest run id."""
    for run in _manifest()["runs"]:
        if run["run_id"] == run_id:
            return ROOT / run["judged"]["path"]
    raise KeyError(f"{run_id} is not in {MANIFEST.name}")


def read_judged(run_id: str) -> list[dict]:
    with judged_path(run_id).open() as fh:
        return [json.loads(line) for line in fh if line.strip()]


def save(fig, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.pdf"
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------
# figure 2 -- harm by condition and tier, treatments between floor and ceiling
# --------------------------------------------------------------------------

TREATMENTS = ("C2", "C3", "C5")
REFERENCES = ("C1", "C6")
HARM_YMAX = 70.0  # C1 on Tier D is 63.4; 0-100 wastes a third of every panel


def fig_headline() -> None:
    """Treatment bars against the untreated floor and the healthy ceiling.

    The claim is a within-panel one: identical corrective content, delivered
    three ways, lands somewhere between an untreated organism and an
    un-fine-tuned model. Drawing C1 and C6 as reference rules rather than bars
    says that directly and cuts the categorical load from five marks to three.

    The y axis is shared across panels. Tier C's bars are genuinely small in
    absolute terms and the figure should show that rather than rescale it away.
    """
    fig, axes = plt.subplots(1, 3, figsize=(TEXTWIDTH_IN, 2.35), sharey=True)
    x = range(len(TREATMENTS))

    for ax, (group, _tier, title) in zip(axes, TIERS):
        harm = read_frozen(group)["harm"]

        for cond in REFERENCES:
            e = harm[cond]
            ax.axhline(
                e.point, color=PALETTE[cond], lw=1.0, ls=(0, (4, 2)), zorder=1
            )
            # Label above the rule, except the ceiling on the baseline.
            offset = 1.6 if cond == "C1" else 1.4
            ax.text(
                len(TREATMENTS) - 0.42, e.point + offset, f"{e.point:.1f}",
                ha="right", va="bottom", fontsize=7, color=PALETTE[cond],
            )

        for i, cond in enumerate(TREATMENTS):
            e = harm[cond]
            ax.bar(
                i, e.point, width=0.62, color=PALETTE[cond],
                hatch=HATCH.get(cond), edgecolor=SURFACE, linewidth=0.8, zorder=2,
            )
            ax.errorbar(
                i, e.point, yerr=[[e.point - e.lo], [e.hi - e.point]],
                fmt="none", ecolor=INK, elinewidth=0.8, capsize=2,
                capthick=0.8, zorder=3,
            )
            ax.text(
                i, e.hi + 1.6, f"{e.point:.1f}", ha="center", va="bottom",
                fontsize=7.5, color=INK, zorder=4,
            )

        ax.set_xticks(list(x))
        ax.set_xticklabels([c for c in TREATMENTS])
        ax.set_xlim(-0.6, len(TREATMENTS) - 0.4)
        ax.set_ylim(0, HARM_YMAX)
        ax.set_title(title, color=INK, pad=5)
        ax.tick_params(length=2.5)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True)

    axes[0].set_ylabel("harm rate (%)")

    handles = [
        Patch(facecolor=PALETTE[c], hatch=HATCH.get(c), edgecolor=SURFACE,
              label=LABELS[c]) for c in TREATMENTS
    ] + [
        Line2D([], [], color=PALETTE[c], lw=1.0, ls=(0, (4, 2)), label=LABELS[c])
        for c in REFERENCES
    ]
    fig.legend(
        handles=handles, loc="lower center", ncol=5,
        bbox_to_anchor=(0.5, -0.10), columnspacing=1.4, handlelength=1.6,
    )
    fig.text(
        0.5, -0.19,
        "Whiskers are BCa 95% intervals, 2,000 probe-clustered draws, seed 0. "
        "Shared y axis. C4 omitted: byte-identical to C3.",
        ha="center", va="top", color=MUTED, fontsize=7,
    )
    fig.tight_layout(w_pad=1.1)
    save(fig, "fig2_harm_by_tier")


# --------------------------------------------------------------------------
# figure 3 -- paired differences against C3
# --------------------------------------------------------------------------

CONTRASTS = ("C3-C1", "C3-C2", "C3-C5", "C3-C6")


def fig_contrasts() -> None:
    """Paired harm differences as a forest plot.

    Every claim in Results turns on whether an interval covers zero, so the
    interval is the mark and zero is the rule.
    """
    fig, axes = plt.subplots(1, 3, figsize=(TEXTWIDTH_IN, 1.95), sharey=True)

    for ax, (group, _tier, title) in zip(axes, TIERS):
        est = read_frozen(group)["harm_diff"]
        for row, contrast in enumerate(CONTRASTS):
            e = est[contrast]
            y = len(CONTRASTS) - row - 1
            color = PALETTE[contrast.split("-")[1]]  # the comparison carries it
            covers_zero = e.lo <= 0 <= e.hi
            ax.plot([e.lo, e.hi], [y, y], color=color, lw=1.5,
                    solid_capstyle="round", zorder=2)
            ax.plot([e.point], [y], "o", ms=4.5, color=color,
                    markerfacecolor=SURFACE if covers_zero else color,
                    markeredgewidth=1.2, zorder=3)

        ax.axvline(0, color=RULE, lw=0.7, zorder=1)
        ax.set_title(title, color=INK, pad=5)
        ax.set_yticks(range(len(CONTRASTS)))
        ax.set_yticklabels(
            [f"C3 − {c.split('-')[1]}" for c in reversed(CONTRASTS)]
        )
        ax.set_xlabel("harm difference (pp)")
        ax.tick_params(length=2.5)

    axes[0].set_ylim(-0.6, len(CONTRASTS) - 0.4)
    fig.text(
        0.5, -0.14,
        "Negative favours C3. Hollow markers mark intervals covering zero. "
        "BCa 95%, 2,000 shared paired draws, seed 0; x scales differ by panel.",
        ha="center", va="top", color=MUTED, fontsize=7,
    )
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig3_paired_contrasts")


# --------------------------------------------------------------------------
# figure 4 -- the coherence floor sits on a mass point
# --------------------------------------------------------------------------

COHERENCE_PANELS = (
    ("Tier C — non-clinical", {"C1": "tier_c_c1", "C3": "tier_c_c3"}),
    ("Tier O — benign clinical", {"C1": "tier_o_c1", "C3": "tier_o_c3"}),
)
FLOOR = 50.0


def fig_coherence_masspoint() -> None:
    """The judge's coherence output, and where the `derailed` rule cuts it.

    Plotted as discrete spikes rather than a histogram because the judge does
    not emit a continuous score -- essentially every value is a multiple of five.
    That quantization is the argument, so binning it away would hide the finding.
    Shown as a share of each run's responses because the two tiers have 240 and
    1,800 rows; raw counts at the floor are annotated on the marks.
    """
    fig, axes = plt.subplots(1, 2, figsize=(TEXTWIDTH_IN, 2.4), sharey=True)
    ymax = 68.0  # tallest spike is 60.4% (Tier C, C3 at 100); leave callout room

    for ax, (title, runs) in zip(axes, COHERENCE_PANELS):
        ax.axvspan(-3, FLOOR + 2.5, color="#f2f1ec", zorder=0, lw=0)
        ax.axvline(FLOOR + 2.5, color=RULE, lw=0.7, ls=(0, (3, 2)), zorder=1)

        # Callouts stack in the empty upper-left rather than floating over the
        # bars; the leader line does the pointing.
        callout_y = (ymax * 0.90, ymax * 0.78)
        for (offset, cond), text_y in zip(((-1.15, "C1"), (1.15, "C3")), callout_y):
            rows = read_judged(runs[cond])
            counts = collections.Counter(
                r["coherence"] for r in rows if r.get("coherence") is not None
            )
            total = sum(counts.values())
            ax.bar(
                [v + offset for v in counts],
                [100.0 * n / total for n in counts.values()],
                width=2.2, color=PALETTE[cond], edgecolor=SURFACE,
                linewidth=0.4, zorder=2,
            )
            at_floor = counts.get(FLOOR, 0)
            # No leader line: at this x a leader is a tall thin stroke that
            # reads as another bar. The shading and the "at exactly 50" wording
            # already point at the mark.
            ax.text(
                1.0, text_y, f"{cond}: {at_floor:,} of {total:,} at exactly 50",
                ha="left", va="center", fontsize=7, color=PALETTE[cond], zorder=5,
            )

        ax.set_title(title, color=INK, pad=5)
        ax.set_xlabel("judge coherence score")
        ax.set_xlim(-3, 103)
        ax.set_ylim(0, ymax)
        ax.tick_params(length=2.5)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True)

    axes[0].set_ylabel("share of responses (%)")
    for ax in axes:
        ax.text(
            FLOOR + 1.0, ymax * 0.985, "derailed (≤ 50)",
            ha="right", va="top", fontsize=7, color=MUTED,
        )
    handles = [
        Patch(facecolor=PALETTE[c], edgecolor=SURFACE, label=LABELS[c])
        for c in ("C1", "C3")
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.07), columnspacing=1.4, handlelength=1.6)
    fig.text(
        0.5, -0.15,
        "Shaded region leaves the harm denominator. The floor is inclusive, so a "
        "single comparison operator decides the mass point at exactly 50.",
        ha="center", va="top", color=MUTED, fontsize=7,
    )
    fig.tight_layout(w_pad=1.2)
    save(fig, "fig4_coherence_floor")


# --------------------------------------------------------------------------
# figure 5 -- session turns displacing corpus notes
# --------------------------------------------------------------------------

DISPLACEMENT_RUNS = {"C3": "tier_d_c3", "C5": "tier_d_c5"}
SESSION_PREFIX = "sess-"


def _session_slots(row: dict) -> int:
    return sum(
        str(nid).startswith(SESSION_PREFIX) for nid in row.get("retrieved_note_ids", [])
    )


def fig_session_displacement() -> None:
    """Tier D harm against the number of retrieval slots taken by session turns.

    Retrieval is query-conditioned on the probe, so all ten samples of a probe
    share one slot allocation; the probe is the unit that gets a dose. Harm uses
    `harness.judge.harm_rate` with the frozen Tier D refusal policy, computed on
    the stored verdicts -- not re-judged.
    """
    fig, ax = plt.subplots(figsize=(3.6, 2.5))
    series: dict[str, tuple] = {}

    for cond, run_id in DISPLACEMENT_RUNS.items():
        rows = read_judged(run_id)
        by_probe: dict[str, list[dict]] = collections.defaultdict(list)
        for row in rows:
            by_probe[row["probe_id"]].append(row)

        buckets: dict[int, list[dict]] = collections.defaultdict(list)
        probes: collections.Counter = collections.Counter()
        for probe_id, probe_rows in by_probe.items():
            slots = _session_slots(probe_rows[0])
            buckets[slots].extend(probe_rows)
            probes[slots] += 1

        xs = sorted(buckets)
        ys = [100.0 * harm_rate([r["verdict"] for r in buckets[k]], "D")[0] for k in xs]
        series[cond] = (xs, ys, probes)
        ax.plot(
            xs, ys, marker="o", ms=4.5, color=PALETTE[cond],
            markerfacecolor=SURFACE if cond == "C5" else PALETTE[cond],
            markeredgewidth=1.2, label=LABELS[cond], zorder=3,
        )

    # Label on the side facing away from the other series, so the two never
    # collide where the lines cross at one slot.
    for cond, (xs, ys, probes) in series.items():
        other = dict(zip(*series["C5" if cond == "C3" else "C3"][:2]))
        for k, y in zip(xs, ys):
            above = y >= other.get(k, y - 1)
            ax.annotate(
                f"{y:.1f}\nn={probes[k]}", xy=(k, y),
                xytext=(0, 8 if above else -19), textcoords="offset points",
                ha="center", va="bottom" if above else "bottom",
                fontsize=7, color=PALETTE[cond], linespacing=1.2, zorder=4,
            )

    ax.set_xlabel("session turns occupying the probe's three retrieval slots")
    ax.set_ylabel("Tier D harm rate (%)")
    ax.set_xticks([0, 1, 2, 3])
    ax.set_xlim(-0.35, 3.35)
    ax.set_ylim(0, 62)
    ax.tick_params(length=2.5)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True)
    ax.legend(loc="upper left", handlelength=1.6)
    fig.text(
        0.5, -0.06,
        "n is probes in the bucket; each contributes ten responses.",
        ha="center", va="top", color=MUTED, fontsize=7,
    )
    fig.tight_layout()
    save(fig, "fig5_session_displacement")


FIGURES = {
    "headline": fig_headline,
    "contrasts": fig_contrasts,
    "coherence": fig_coherence_masspoint,
    "session": fig_session_displacement,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fig", choices=sorted(FIGURES), action="append")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    names = sorted(FIGURES) if args.all else (args.fig or sorted(FIGURES))
    with plt.rc_context(RC):
        for name in names:
            FIGURES[name]()


if __name__ == "__main__":
    main()

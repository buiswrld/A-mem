import json
import random
from collections import defaultdict

PATH = "medmcqa/train.json"
N = 50
SEED = 12080

def load():
    with open(PATH) as f:
        return [json.loads(l) for l in f if l.strip()]


def sample(rows, n, seed):
    rng = random.Random(seed)
    by_subject = defaultdict(list)
    for r in rows:
        by_subject[r["subject_name"]].append(r)
    return rng.sample(rows,50)

def main():
    rows = load()
    picked = sample(rows, N, SEED)
    with open(f"sample.json", "w") as f:
        json.dump(picked, f, indent=2)
    print(f"wrote {len(picked)} rows")


if __name__ == "__main__":
    main()

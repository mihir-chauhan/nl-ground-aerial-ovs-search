"""Paired episode-level comparison of two systems on shared layouts.

    python method/analyze.py --a search_nl --b search_sym --task relational --seed 0 --out m.json

Reads the per-episode CSVs written by method/search.py (results/raw/<prefix>_<task>_s<seed>_episodes.csv,
seeds 0-4), pairs episodes by (seed, episode index) and reports the mean difference A minus B in
steps-to-find and success with a 95% percentile bootstrap interval over paired episodes and a
two-sided sign-flip permutation p-value on steps. `--task all` pools the four tiers;
`--task all --contrast` is (attribute + relational) minus (exact + synonym) of the A-minus-B step
difference. `--a2/--b2` subtract a second pair (difference of differences, e.g. corrupted minus clean).
"""
import argparse
import csv
import json

import numpy as np

TIERS = ["exact", "synonym", "attribute", "relational"]
SEEDS = [0, 1, 2, 3, 4]


def load(prefix, task):
    rows = {}
    for s in SEEDS:
        with open("results/raw/%s_%s_s%d_episodes.csv" % (prefix, task, s)) as f:
            for r in csv.DictReader(f):
                rows[(task, s, int(r["ep"]))] = (float(r["steps"]), float(r["success"]), r["tier"])
    return rows


def diff(a, b, tasks):
    A, B = {}, {}
    for t in tasks:
        A.update(load(a, t))
        B.update(load(b, t))
    keys = sorted(A)
    assert keys == sorted(B)
    d_steps = np.array([A[k][0] - B[k][0] for k in keys])
    d_succ = np.array([A[k][1] - B[k][1] for k in keys])
    tier = np.array([A[k][2] for k in keys])
    return d_steps, d_succ, tier


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--a2")
    ap.add_argument("--b2")
    ap.add_argument("--task", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--contrast", action="store_true", help="with --task all: open minus closed tiers")
    a = ap.parse_args()
    if a.contrast:
        a.task = "interaction"
    rng = np.random.default_rng(a.seed)
    tasks = TIERS if a.task in ("all", "interaction") else [a.task]
    ds, dc, tier = diff(a.a, a.b, tasks)
    if a.a2:
        ds2, dc2, _ = diff(a.a2, a.b2, tasks)
        ds, dc = ds - ds2, dc - dc2
    n = len(ds)
    if a.task == "interaction":
        open_ = np.isin(tier, ["attribute", "relational"])
        stat = lambda x, idx: x[idx][open_[idx]].mean() - x[idx][~open_[idx]].mean()
    else:
        stat = lambda x, idx: x[idx].mean()
    full = np.arange(n)
    idx = rng.integers(0, n, (a.boot, n))
    bs = np.array([stat(ds, i) for i in idx])
    bc = np.array([stat(dc, i) for i in idx])
    obs = stat(ds, full)
    # sign-flip permutation test on the paired step differences
    if a.task == "interaction":
        w = np.where(open_, 1.0 / open_.sum(), -1.0 / (~open_).sum())
    else:
        w = np.full(n, 1.0 / n)
    flips = rng.choice([-1.0, 1.0], (a.boot, n))
    perm = (flips * (ds * w)).sum(1)
    p = float((np.abs(perm) >= abs(obs) - 1e-12).mean())
    out = dict(d_steps=float(obs), d_steps_lo=float(np.percentile(bs, 2.5)),
               d_steps_hi=float(np.percentile(bs, 97.5)), d_success=float(stat(dc, full)),
               d_success_lo=float(np.percentile(bc, 2.5)), d_success_hi=float(np.percentile(bc, 97.5)),
               p_steps=p, n_pairs=float(n))
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()

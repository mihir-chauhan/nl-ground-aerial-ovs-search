"""Entrypoint of the ground-aerial search study: one system on one task for one seed.

    python method/search.py --system nl --task relational --seed 0 --out metrics.json

`--task` is a query tier (exact, synonym, attribute, relational), `mixed` (episodes cycle
through the four tiers) or `all` (every episode of all four tiers). Writes a flat JSON of metrics (means over episodes) and, next to
it, a per-episode CSV used by the paired analysis (method/analyze.py).
"""
import argparse
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=sim.SYSTEMS)
    ap.add_argument("--task", required=True, choices=sim.TIERS + ["mixed", "all"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--episodes", type=int, default=40)
    ap.add_argument("--out", required=True)
    for k, v in sim.DEFAULTS.items():
        ap.add_argument("--" + k, type=type(v), default=v)
    a = ap.parse_args()
    P = {k: getattr(a, k) for k in sim.DEFAULTS}
    rows = []
    # `all` runs the full episode set of each of the four tiers (the same episodes as the per-tier tasks)
    plan = ([(t, ep) for t in sim.TIERS for ep in range(a.episodes)] if a.task == "all" else
            [(a.task if a.task != "mixed" else sim.TIERS[ep % 4], ep) for ep in range(a.episodes)])
    for tier, ep in plan:
        r = sim.run_episode(a.seed, tier, ep, a.system, P)
        r["ep"] = ep
        rows.append(r)
    m = lambda k: float(np.mean([r[k] for r in rows]))
    out = dict(success=m("success"), steps=m("steps"), spl=m("spl"), msgs=m("msgs"),
               tokens=m("tokens"), overlap=m("overlap"), aerial_find=m("aerial_find"))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.splitext(a.out)[0] + "_episodes.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)


if __name__ == "__main__":
    main()

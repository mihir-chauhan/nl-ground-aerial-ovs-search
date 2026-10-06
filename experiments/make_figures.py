"""Figures drawn from results/runs.jsonl only."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False})
runs = [json.loads(l) for l in open("results/runs.jsonl")]
runs = [r for r in runs if r.get("status") == "ok"]
TIERS = ["exact", "synonym", "attribute", "relational"]


def vals(group, name, task, metric, cfg=None):
    return np.array([r["metrics"][metric] for r in runs if r["group"] == group and r["name"] == name
                     and r["task"] == task and (cfg is None or all(r["config"].get(k) == v for k, v in cfg.items()))])


# Figure 1: steps and success by tier and system
systems = ["NL messaging", "Symbolic messaging", "Oracle sharing", "Frontier team, no comm",
           "Single ground frontier", "Random-walk team"]
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.5))
for ax, metric, lab in zip(axes, ["steps", "success"], ["steps to find (censored at cap)", "success rate"]):
    w = 0.13
    for i, s in enumerate(systems):
        m = [vals("main", s, t, metric).mean() for t in TIERS]
        e = [vals("main", s, t, metric).std(ddof=1) for t in TIERS]
        ax.bar(np.arange(4) + (i - 2.5) * w, m, w * 0.86, yerr=e, color=PAL[i], label=s,
               error_kw=dict(ecolor=INK, lw=0.6, capsize=1.2))
    ax.set_xticks(np.arange(4))
    ax.set_xticklabels(TIERS)
    ax.set_ylabel(lab)
    ax.grid(axis="x", visible=False)
axes[0].set_ylim(40, 102)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, ncol=6, loc="upper center", fontsize=6.5, bbox_to_anchor=(0.5, 1.03), handlelength=1.2, columnspacing=1.0)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("results/figures/fig_tiers.pdf")

# Figure 2: paired differences against symbolic messaging, per tier
comps = [("NL minus Symbolic", "NL (room names)"), ("NL+coords minus Symbolic", "NL + coordinates"),
         ("Symbolic+conf minus Symbolic", "Symbolic + confidence")]
cols = TIERS + ["all"]
fig, ax = plt.subplots(figsize=(3.45, 2.5))
for i, (name, lab) in enumerate(comps):
    xs = np.arange(len(cols)) + (i - 1) * 0.22
    d = np.array([vals("paired", name, t, "d_steps")[0] for t in cols])
    lo = np.array([vals("paired", name, t, "d_steps_lo")[0] for t in cols])
    hi = np.array([vals("paired", name, t, "d_steps_hi")[0] for t in cols])
    ax.errorbar(xs, d, yerr=[d - lo, hi - d], fmt="o", ms=4, color=PAL[i], ecolor=PAL[i], lw=1.2, capsize=2, label=lab)
ax.axhline(0, color=INK, lw=0.8)
ax.set_xticks(np.arange(len(cols)))
ax.set_xticklabels(cols)
ax.set_ylabel("steps: system minus symbolic\n(below 0 = faster than symbolic)")
ax.grid(axis="x", visible=False)
ax.set_ylim(-8.5, 4.6); ax.legend(fontsize=6.5, loc="lower left")
fig.tight_layout()
fig.savefig("results/figures/fig_paired.pdf")

# Figure 3: corruption sweep
fig, axes = plt.subplots(1, 2, figsize=(3.45, 2.1), sharex=True)
ps = [0.0, 0.1, 0.2, 0.4]
for ax, metric, lab in zip(axes, ["steps", "success"], ["steps to find", "success rate"]):
    for i, s in enumerate(["NL messaging", "Symbolic messaging"]):
        m = np.array([vals("sweep_corrupt", s, "mixed", metric, {"corrupt": p}).mean() for p in ps])
        e = np.array([vals("sweep_corrupt", s, "mixed", metric, {"corrupt": p}).std(ddof=1) for p in ps])
        ax.errorbar(np.array(ps) + (i - 0.5) * 0.012, m, yerr=e, color=PAL[i], marker="o", ms=4, lw=2, capsize=2, label=s.split()[0])
    ax.set_xlabel("corruption rate")
    ax.set_ylabel(lab)
    ax.set_xticks(ps)
axes[0].legend(fontsize=6.5)
fig.tight_layout()
fig.savefig("results/figures/fig_corrupt.pdf")

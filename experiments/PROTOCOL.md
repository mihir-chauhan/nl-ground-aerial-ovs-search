# Protocol

- **Tasks.** Four query tiers (exact, synonym, attribute, relational), 40 episodes per tier and seed in
  the main comparison; `mixed` (episodes cycle through the tiers, 80 episodes per seed) for sweeps.
- **Seeds.** 0-4 for every reported run. World, perception noise and corruption noise are functions of
  (seed, tier, episode) only, so every system sees the same layouts and the same sensor noise (paired).
- **Development.** Seeds 100-102 were used to debug and to set the step cap (100, chosen so that the
  single-ground baseline succeeds in roughly half of the episodes; at cap 200 everything saturates). All
  detector, sensing and channel parameters were set before looking at seeds 0-4 and were not changed
  afterwards. No parameter was tuned per system.
- **Metrics.** success (found within cap), steps (cap if not found), spl (success x shortest ground path /
  steps), msgs and tokens per episode (words for NL, fields for symbolic), overlap (Jaccard of the cells
  ever sensed by the two robots), aerial_find (share of episodes ended by an aerial verification).
- **Statistics.** Mean and std over 5 seeds (`rh table`), seed-level tests (`rh compare`), and paired
  episode-level differences with 95% percentile bootstrap intervals (10000 resamples) and sign-flip
  permutation p-values (`method/analyze.py`, groups `paired`, `paired_sweeps`).
- **Groups.** `main` (six systems on the four tiers, on `all` = the same 4 x 40 episodes pooled, and on
  `mixed`), `content` (decomposition), `abl_team`, `sweep_K`, `sweep_corrupt`, `sweep_res`, `sweep_noise`,
  `paired`, `paired_sweeps`, `smoke`. Group `search` is the first logging of the four tier tasks; `main`
  repeats those runs with identical metrics (the harness expects the method in a group called `main`), and
  the per-episode CSVs written by `search` and `content` runs are the input of the paired analysis.
- **Order.** `experiments/run_main.sh 0 1 2 3 4`; `run_ablations.sh content|team|team_prio|sweeps1|sweeps2`;
  then `run_analysis.sh` (needs the per-episode CSVs under `results/raw/`, which git ignores) and
  `make_figures.py`. The paired rows were logged twice: the first version used a task called `interaction`;
  it was superseded and re-logged as "<pair>, open minus closed tiers" on task `all` (same computation,
  same numbers). `paired_sweeps` rows therefore appear twice with identical values.
- **Hardware.** One shared CPU machine, 2 threads; about 30 minutes of experiments in total, including the repeated `main` logging.
- **Foreign rows.** Groups `main` and `sweep_beta` in `results/runs.jsonl` (GD, Momentum, Adam) come from
  an unrelated platform demonstration written into this workspace by another process. They are not part of
  this study, were retired with `rh supersede` (the rows stay in the file), and no number from them is
  used. Files of that demonstration (`method/run.py`, `results/figures/*steps_to_tol*`, `sweep_beta*`)
  were left in place.
- **Late addition.** The `team_prio` runs were added after the team ablation showed a livelock of the
  mutual avoidance rule in same-type teams (see `method/DESIGN.md`).

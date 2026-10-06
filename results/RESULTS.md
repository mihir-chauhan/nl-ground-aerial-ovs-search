# Results

All numbers below are in `results/runs.jsonl` (groups `main`, `content`, `paired`, `paired_sweeps`,
`abl_team`, `sweep_*`); tables in `results/tables/`, figures in `results/figures/`. Paired differences are
episode-level, A minus B on identical layouts, with 95% bootstrap intervals (`method/analyze.py`).
Rows of groups `main`/`sweep_beta` named GD, Momentum, Adam are an unrelated platform demonstration that
another process wrote into this workspace; they are marked superseded and are not used.

## H1 (NL beats symbolic in success and steps at equal message budget): NOT SUPPORTED on steps, small gain in success
- `paired`, "NL minus Symbolic", task `all`: steps +1.28 [0.42, 2.16] (NL slower); success +2.0 points [0.4, 3.8].
- `main`, task `all`: NL 64.12 +- 0.59 steps vs symbolic 62.84 +- 1.26; seed-level paired p = 0.015 (5 seeds).
- NL uses about twice the tokens (72.0 vs 36.3 per episode on `all`).

## H2 (advantage grows with open-vocabulary queries, vanishes or reverses for exact names): SUPPORTED IN DIRECTION
- `paired`, "NL minus Symbolic" steps: exact +2.98 [2.03, 4.01], synonym +2.08 [0.95, 3.19],
  attribute +1.27 [-0.94, 3.48], relational -1.23 [-3.38, 0.78].
- Open minus closed tiers contrast: -2.51 [-4.21, -0.86] steps.
- Success: relational +7.0 points [3.0, 11.0], attribute +4.0 [-0.5, 8.5], exact and synonym -1.5 [-4.0, 0.5].
- Qualifications: the synonym tier behaves like the exact tier; NL is never clearly faster than symbolic.

## H3 (NL advantage shrinks under corruption): NOT SUPPORTED AS STATED
- `paired_sweeps`, mixed task: NL minus symbolic steps at corruption 0 / 0.1 / 0.2 / 0.4 =
  +1.51 [0.26, 2.75] / -0.68 [-2.90, 1.58] / -0.86 [-3.36, 1.62] / -0.03 [-2.46, 2.37].
- There is no advantage to shrink; the gap moves toward NL if at all (shift at 0.1: -2.19 [-4.33, -0.04];
  at 0.2 and 0.4 the interval includes zero). Both channels degrade (at 0.4: NL +9.68, symbolic +11.22 steps).

## Decomposition (group `content`, `paired`)
- NL + coordinates and Symbolic + attributes are identical in every cell (lossless template and parser):
  -1.00 [-1.71, -0.34] steps vs symbolic pooled. Symbolic + confidence: -0.98 [-1.72, -0.25].
- Room name instead of coordinates (NL minus NL + coordinates): +2.28 [1.79, 2.80] steps pooled.

## Other
- Communication vs none (pooled): symbolic -8.46 [-10.20, -6.74], NL -7.18 [-8.78, -5.62] steps.
- Symbolic messaging lowers success below no-comm on relational queries: -5.5 points [-11.0, -0.5].
- Sensitivity (K, aerial resolution, detector noise): NL minus symbolic stays between about +1.0 and +1.9
  steps; several intervals touch zero, none favours NL.
- Team ablation: the mutual room-avoidance rule livelocks in same-type teams (two ground robots with NL:
  0.28 success vs 0.53 without a channel). A priority rule, added after seeing this, fixes it (0.77
  success, 63.86 steps) and puts two ground robots close to the ground-aerial team (0.85, 60.81).
- Sanity ordering holds in every tier: oracle >= messaging > no-comm team > single ground > random walk.
- `rh verdict`: tier 0 (the method is not the best system on the primary task), which matches the finding.

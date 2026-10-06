# Verdict: tier 0 (not best) — target tier 2 (solid)

Method: NL messaging | primary metric: steps | primary task: mixed

| Task | Ours | Best baseline | Their mean | Rel. gain | p | Cohen d | n |
|---|---|---|---|---|---|---|---|
| all | 64.12 | Oracle sharing | 60.77 | -5.5% | 0.00604 | -2.57 | 5 |
| attribute | 66.65 | Oracle sharing | 61.98 | -7.5% | 0.00396 | -1.32 | 5 |
| exact | 61.54 | Oracle sharing | 58.21 | -5.7% | 0.0491 | -1.55 | 5 |
| mixed | 60.81 | Oracle sharing | 58.57 | -3.8% | 0.0798 | -0.76 | 5 |
| relational | 61.98 | Oracle sharing | 60.12 | -3.1% | 0.106 | -0.56 | 5 |
| synonym | 66.29 | Oracle sharing | 62.74 | -5.7% | 0.0252 | -0.64 | 5 |

| Ablation | Delta vs full | p | Matters? |
|---|---|---|---|
| NL + coordinates | +2.284 | 2.96e-08 | NO |
| Symbolic + attributes | +2.284 | 2.96e-08 | NO |
| Symbolic + confidence | +2.259 | 4.6e-08 | NO |
| NL, two ground robots | -27.56 | 7.63e-06 | yes |
| NL, two aerial robots | -37.61 | 5.35e-06 | yes |
| NL, priority rule | -2.355 | 0.0307 | yes |

## Why this tier
- not best on mixed: ours 60.81 vs Oracle sharing 58.57

## To reach the next tier
- beat the best baseline on the primary task

TARGET NOT REACHED

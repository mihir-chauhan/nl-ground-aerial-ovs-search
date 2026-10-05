| Method | Task | steps_to_tol | final_loss | n |
|---|---|---|---|---|
| GD | cond10 | **42.000 ± 3.606** | **-0.000 ± 0.000** | 3 |
| Adam | cond10 | 100.667 ± 2.082 | 0.000 ± 0.000 | 3 |
| Momentum | cond10 | _90.333 ± 2.082_ | _0.000 ± 0.000_ | 3 |
| GD | cond1000 | 400.000 ± 0.000 | 1.112 ± 0.762 | 3 |
| Adam | cond1000 | **136.667 ± 16.258** | **0.000 ± 0.000** | 3 |
| Momentum | cond1000 | _300.000 ± 39.000_ | _0.000 ± 0.000_ | 3 |

Mean ± std over seeds; bold = best, underline = second. Directions: steps_to_tol ↓, final_loss ↓.

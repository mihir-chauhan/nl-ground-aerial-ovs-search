# Design

Entrypoint of this study: `method/search.py --system <s> --task <tier|mixed> --seed <n> --out <json>`
(simulator in `method/sim.py`, paired analysis in `method/analyze.py`).
`method/run.py` is NOT part of this study: it belongs to an unrelated platform demonstration (gradient
descent on least squares) that another process committed into this workspace (commits 94b04ea, d3dc894);
it is left untouched so that the demonstration's logged commands still reproduce.

## World
30x30 grid, recursive rectangular split into 4-8 rooms (walls with one or two doors), rooms named from a
fixed list, each covered ("roofed", invisible to the aerial robot) with probability 0.3. 1-2 landmarks per
room (sofa, table, bed, shelf, desk). 12 small objects: the target, two distractors, nine fillers; 20
classes in 5 similarity groups of 4, one synonym per class, 6 colours. The floor plan (walls, room names,
roofs) is known to both robots; object positions are not.

Query tiers: exact ("the mug"), synonym ("the cup"), attribute ("the red mug", two other-colour mugs
present), relational ("the mug near the sofa", two mugs away from any sofa present). In the exact and
synonym tiers the two distractors are other classes of the same similarity group.

## Simulated open-vocabulary detector
Fixed random 64-d word embeddings (seed 12345); classes in a group share a component (cosine about 0.36),
synonyms are noisy copies of the class vector. Score = mean over the query's slots (class, colour,
landmark) of the cosine between query word and perceived word; an unknown slot scores 0.5, an absent
landmark 0. Gaussian noise is added (ground 0.05, aerial 0.10).

## Robots
| | ground | aerial |
|---|---|---|
| speed | 1 cell/step, 4-connected, walls block | 2 cells/step, flies over walls |
| sensing | Chebyshev radius 3, same room | Chebyshev radius 4, not under roofs |
| label | exact | confused within the group w.p. 0.2 |
| colour | exact | perceived w.p. 0.7 |
| position | exact | quantised to 3x3 blocks |
| verification | adjacent, 3 steps | after its coverage is complete: descend, 10 steps |

Exploration: nearest unsensed cell (coverage frontier, goal kept until sensed); +15 cost on cells of the
room the teammate announced. When nothing is left the coverage map is reset (new pass, fresh noise).
Ground priority: own candidates (score >= 0.75) > remote candidates (utility = score - distance/50) >
frontier. A remote candidate is a region (3x3 block around coordinates, or a whole room) and is resolved
when the ground robot has sensed all of it.

## Channels
A robot may send one message every K=5 steps with at most M=2 sightings plus its intent (when changed).
The aerial robot reports each object whose class-slot score + noise >= 0.6, best first. Receiver keeps an
entry if its re-scored value >= 0.7.
- `nl` (ours): "i am heading to the office . i see a red mug near the sofa in the kitchen and a mug in the lab"; keyword parser; location = room.
- `nl_coords`: same, plus "at x y".
- `sym`: `(G, x, y)`, `(S, class, x, y)`; colour/landmark slots unknown (0.5) at the receiver.
- `sym_attr`: adds colour id and landmark id fields. `sym_score`: adds the sender's score, used as is.
- `oracle`: records passed losslessly every step, no entry limit.
- Corruption p: NL: each room word replaced by another room w.p. p, then each word dropped w.p. p.
  Symbolic: each coordinate pair replaced by a random cell w.p. p, then each field erased w.p. p (a tuple
  with an erased required field is discarded).

## Known flaw found during the study
The mutual room-avoidance rule livelocks when two identical robots start on the same cell (both yield in
lockstep). It does not occur for the ground-aerial team. `--prio 1` (only the second robot yields)
removes it; both variants are reported in the team ablation. The main configuration keeps `prio=0`.

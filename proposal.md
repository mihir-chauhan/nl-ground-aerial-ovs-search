# Proposal: natural-language versus symbolic messaging for ground-aerial open-vocabulary search

## Direction (verbatim from user)
Create a framework that has heterogeneous collaboration for open vocab search with ground and aerial
robots talk in natural language

## Question
In a simulated grid world, does natural-language communication between a ground robot and an aerial
robot improve open-vocabulary object search success and time-to-find compared with fixed-schema symbolic
messaging and with non-communicating frontier exploration?

## Hypotheses (fixed in the approved brief before any run)
| ID | Hypothesis | Experiment group | Metric | Refuted if |
|---|---|---|---|---|
| H1 | NL team beats the symbolic team in success and steps at equal message budget | `search`, `paired` (task all) | success, steps | pooled paired difference is zero or favours symbolic |
| H2 | NL advantage grows from exact to synonym/attribute/relational queries, vanishing or reversing for exact names | `paired` per tier + interaction | steps, success | interaction CI includes zero or has the wrong sign |
| H3 | NL advantage shrinks under message corruption | `sweep_corrupt`, `paired_sweeps` | steps | NL-minus-symbolic does not move toward symbolic as corruption grows |

## Method
Scripted ground robot (slow, short range, sees colour and exact position, verifies at close range) and
aerial robot (fast, wide footprint, coarse position, confusable labels, colour only sometimes, blind
under roofs). Both explore by nearest-frontier coverage. The aerial robot reports sightings of the queried
class; the channel is the only thing that changes: templated English sentences with room-name locations
read by a keyword parser (ours), or `(class id, x, y)` tuples (baseline). The receiver re-scores what the
message says against the query with the same slot-wise embedding scorer as the simulated detector.

## Baselines (all reimplemented here)
Symbolic messaging; frontier team without communication; single ground robot; random-walk team; oracle
sharing (lossless, unlimited, every step).

## Ablations
Content/format decomposition (NL + coordinates, symbolic + attribute fields, symbolic + sender
confidence); message budget K; corruption rate; aerial resolution; detector noise; team composition.

## Risks
The NL channel is templated, so this tests information format, not LLM behaviour. The symbolic schema can
always be extended; the decomposition ablation measures exactly that.

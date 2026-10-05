# Natural-Language versus Symbolic Messaging for Ground-Aerial Open-Vocabulary Search in a Toy World

## Seed
Create a framework that has heterogeneous collaboration for open vocab search with ground and aerial robots talk in natural language

## Clarifications
- **What is the core hypothesis or contribution you want to test?** Natural-language communication between heterogeneous robots yields higher search success and lower time-to-find than structured or symbolic message passing.
- **What environment or benchmark should the search task run in?** A 2D/3D grid or top-down semantic map world I build, with simulated sensors, for a fast CPU study.
- **What should "better" mean, and which baselines must the framework beat?** Success and efficiency against classical frontier-based multi-robot exploration plus an open-vocabulary detector (e.g., CLIP or OWL-ViT).
- **Which language and vision models should drive the robots, and are API calls allowed?** Small or scripted language agents with a templated or mock LLM, to keep it a quick CPU prototype.
- **What scope and compute are you willing to accept?** A quick CPU study in minutes to hours, with a toy world, a few dozen episodes and several seeds.

## Research question
In a simulated grid world, does natural-language communication between a ground robot and an aerial robot improve open-vocabulary object search success and time-to-find compared with structured/symbolic messaging and with non-communicating frontier exploration?

## Hypotheses
- H1: A ground-aerial team using templated natural-language messages achieves higher search success rate and lower mean steps-to-find than the same team using structured symbolic messages (fixed-schema coordinates and class IDs), at equal message budget.
- H2: The natural-language advantage over symbolic messaging grows as queries become more open-vocabulary (synonyms, attribute descriptions, relational phrases such as 'the mug near the sofa') and shrinks to zero or reverses for exact in-vocabulary class names.
- H3: The natural-language advantage shrinks under message corruption (dropped words, wrong-room references), which would show that gains depend on message fidelity rather than on the language channel itself.

## Baselines
- Frontier-based multi-robot exploration (Yamauchi 1997; multi-robot cost-utility variant) with an open-vocabulary detector, no communication (reimplemented)
- Frontier exploration with open-vocabulary detector and structured/symbolic message passing (class ID + coordinates) between robots (reimplemented)
- Single ground robot, frontier exploration plus open-vocabulary detector (reimplemented)
- Random-walk team with open-vocabulary detector (reimplemented)
- Oracle-communication upper bound with shared full observations (reimplemented)

## Tasks
- Procedurally generated 2D top-down semantic grid worlds (~30x30, 4-8 rooms, ~20 object categories with attributes and synonyms), CPU only, single target per episode
- Query tiers: exact class name, synonym/paraphrase, attribute description, relational description
- Simulated open-vocabulary detector built on a small text-embedding similarity (CLIP/OWL-ViT-style scoring with noise and confusion between similar classes), with an optional check using a small pretrained text encoder if it fits the CPU budget
- About 30-40 episodes per condition x 5 seeds, with fixed per-episode step cap

## Metrics
- Success rate within step cap (higher is better)
- Time-to-find in steps, with censoring at the cap (lower is better)
- Path efficiency / SPL-style score (higher is better)
- Messages exchanged and tokens per episode (lower is better)
- Redundant-exploration overlap between robots (lower is better)
- Mean and 95% bootstrap CI over seeds, with paired comparisons on shared episode layouts

## Ablations
- Message channel: natural language vs symbolic vs none vs oracle
- Message budget: unlimited vs 1 message per K steps
- Message corruption rate (word dropout and wrong-room references)
- Query tier: exact, synonym, attribute, relational
- Aerial sensor resolution and noise level
- Team composition: ground+aerial vs two ground vs two aerial
- Detector noise level

## Plan
- Implement the world generator, ground and aerial sensor models, and the simulated open-vocabulary detector with a synonym/attribute vocabulary
- Implement frontier-based exploration and the no-communication, single-robot, random, and oracle baselines; sanity-check that oracle > team > single > random
- Implement the symbolic channel and the templated natural-language channel with a rule-based parser (mock LLM), keeping information content matched and documenting any mismatch
- Run the main comparison across query tiers, 5 seeds, paired layouts, with episode and time budget checks
- Run the message budget, corruption, sensor and team-composition ablations
- Compute bootstrap CIs and paired tests, plot success and steps-to-find by condition and query tier, and report null or negative results as found
- Write up with explicit limits: the NL channel is templated, so it tests the information-format hypothesis, not real LLM behavior

## Out of scope
- Real LLM or API calls, and fine-tuned language or vision models
- Real images, photorealistic 3D simulation, or physical robots
- Learned communication protocols or RL training
- SLAM, localization error, and dynamic obstacles or moving targets
- Teams larger than two or three robots, and multi-target tasks
- Claims about real-world transfer or about free-form LLM dialogue quality

## Method
Build a top-down semantic grid world (rooms, furniture, objects with attributes) with a ground robot (limited field of view, can traverse clutter, close-range sensing) and an aerial robot (wide field of view, coarse low-resolution semantic sensing, fast movement, can't see inside occluded areas). Both use a simulated open-vocabulary detector (embedding-similarity scoring of object descriptions against a text query, with noise) and a scripted/templated mock-LLM agent that generates and parses natural-language messages (e.g. 'I see a sofa and a lamp in the north room, no mug yet') and chooses frontier goals from them, compared to a schema-based symbolic channel carrying the same underlying information. Run a few dozen episodes per condition across at least 3 seeds with a hard 45-minute total CPU budget.

Field: robotics
Scale: quick study, cpu, about 35 minutes of experiments.

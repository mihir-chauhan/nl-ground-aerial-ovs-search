# Landscape

Searches run with `rh lit search` (candidates in `literature/candidates.jsonl`): open-vocabulary object
navigation with frontier/language maps; heterogeneous multi-robot collaboration with language models
(air-ground); communication format in embodied multi-agent cooperation; multi-robot frontier exploration
and object search with vision-language models; plus title searches for the detector and metric papers.

## What exists
- **Single-robot open-vocabulary search.** VLFM (arXiv 2312.03275) scores frontiers with a vision-language
  value map; OneMap (2409.11764) keeps a reusable open-vocabulary feature map for multi-object search;
  HOV-SG (2403.17846) builds hierarchical open-vocabulary scene graphs (floor/room/object) for
  language-grounded navigation; HM3D-OVON (2409.14296) is the open-vocabulary ObjectNav benchmark.
  Open-vocabulary detectors such as OWL-ViT (2205.06230) supply the perception.
- **Multi-robot semantic search.** GoalSwarm (2603.12908) coordinates several UAVs on a shared 2D semantic
  map; COMRES-VLM (2509.26324) lets a VLM assign frontiers over shared occupancy maps. Frontier
  exploration methods are benchmarked in Explore-Bench (2202.11931).
- **Language as the inter-robot medium.** Air-ground collaboration for language-specified missions
  (2505.09108) uses LLM planning with a UGV/UAV pair under intermittent communication; MHRC (2409.16030)
  and the centralized-vs-decentralized study (2309.15943) use LLM dialogue among heterogeneous robots and
  examine token cost; CoELA (2307.02485) builds embodied agents that communicate in natural language under
  costly communication; Ask-Reason-Assist (2509.23506) uses NL help requests between heterogeneous robots.
- **Engineered vs learned message content.** "Communicating plans, not percepts" (2508.02912) compares an
  engineered intention message with a learned protocol; the Comm-MADRL survey (2203.08975) classifies what
  agents communicate, to whom, and under what constraints.
- **Metrics.** SPL from "On evaluation of embodied navigation agents" (1807.06757).
- Platform library hits (not citable): none close to this question.

## Closest work
The air-ground language-mission system (2505.09108) and MHRC (2409.16030): both run heterogeneous teams
on natural language but evaluate the full stack. Neither holds agents, sensing and planning fixed while
swapping only the message format, and neither separates message content from location format.

## Gap
No controlled test of *natural-language versus fixed-schema symbolic messages at matched budget* for
ground-aerial open-vocabulary search, across query types that the schema can or cannot express, with
paired layouts. A toy scripted world is enough to test the information-format part of that question
(not LLM behaviour).

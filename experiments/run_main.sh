#!/bin/bash
# Main comparison (group `main`): 6 systems x 5 seeds on the four query tiers (40 episodes each), on
# `all` (the same 4 x 40 episodes pooled) and on `mixed` (80 episodes cycling through the tiers).
# usage: run_main.sh <seed> [<seed> ...]
# The group `search` in results/runs.jsonl is an earlier, identical logging of the four tier tasks; the
# per-episode CSVs it wrote (results/raw/search_*) are the input of the paired analysis.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=${PY:-/Users/pumpkinpies/Donna/Mihir/mihir-s-platform-on-top-his-existing-git/data/envs/sci/bin/python}
run() {  # kind name system group task seed [extra args]
  kind=$1; name=$2; sys=$3; group=$4; task=$5; seed=$6; shift 6
  f=results/raw/${group}_${sys}_${task}_s${seed}.json
  rh run --kind $kind --name "$name" --group $group --task $task --seed $seed --metrics-file $f -- \
    $PY method/search.py --system $sys --task $task --seed $seed --out $f "$@" 2>&1 | grep -E "^\[" | cut -c1-110
}
for seed in "$@"; do
 for task in exact synonym attribute relational all mixed; do
  ex=""; [ $task = mixed ] && ex="--episodes 80"
  run method   "NL messaging"           nl      main $task $seed $ex
  run baseline "Symbolic messaging"     sym     main $task $seed $ex
  run baseline "Frontier team, no comm" nocomm  main $task $seed $ex
  run baseline "Single ground frontier" single  main $task $seed $ex
  run baseline "Random-walk team"       random  main $task $seed $ex
  run baseline "Oracle sharing"         oracle  main $task $seed $ex
 done
done

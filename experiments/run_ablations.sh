#!/bin/bash
# Ablations. usage: run_ablations.sh content|sweeps1|sweeps2|team
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=${PY:-/Users/pumpkinpies/Donna/Mihir/mihir-s-platform-on-top-his-existing-git/data/envs/sci/bin/python}
run() {  # kind name system group task seed tag config [extra args]
  kind=$1; name=$2; sys=$3; group=$4; task=$5; seed=$6; tag=$7; cfg=$8; shift 8
  f=results/raw/${group}_${sys}${tag}_${task}_s${seed}.json
  rh run --kind $kind --name "$name" --group $group --task $task --seed $seed --config "$cfg" --metrics-file $f -- \
    $PY method/search.py --system $sys --task $task --seed $seed --out $f "$@" 2>&1 | grep -E "^\[" | cut -c1-110
}
sweep() {  # param flag values...
  param=$1; shift
  for v in "$@"; do for seed in 0 1 2 3 4; do
    run method   "NL messaging"       nl  sweep_$param mixed $seed _$v "{\"$param\": $v}" --episodes 80 --$param $v
    run baseline "Symbolic messaging" sym sweep_$param mixed $seed _$v "{\"$param\": $v}" --episodes 80 --$param $v
  done; done
}
case $1 in
content)
 for seed in 0 1 2 3 4; do for task in exact synonym attribute relational; do
  run method   "NL messaging"          nl        content $task $seed "" "{}"
  run ablation "NL + coordinates"      nl_coords content $task $seed "" "{}"
  run ablation "Symbolic messaging"    sym       content $task $seed "" "{}"
  run ablation "Symbolic + attributes" sym_attr  content $task $seed "" "{}"
  run ablation "Symbolic + confidence" sym_score content $task $seed "" "{}"
 done; done ;;
sweeps1) sweep K 1 5 10 20; sweep res 1 3 5 ;;
sweeps2) sweep corrupt 0.0 0.1 0.2 0.4; sweep noise 0.0 1.0 2.0 ;;
team)
 for seed in 0 1 2 3 4; do
  run method   "NL messaging"            nl     abl_team mixed $seed _GA '{"team": "GA"}' --episodes 80 --team GA
  run ablation "NL, two ground robots"   nl     abl_team mixed $seed _GG '{"team": "GG"}' --episodes 80 --team GG
  run ablation "NL, two aerial robots"   nl     abl_team mixed $seed _AA '{"team": "AA"}' --episodes 80 --team AA
  run ablation "No comm, two ground robots" nocomm abl_team mixed $seed _GG '{"team": "GG"}' --episodes 80 --team GG
  run ablation "No comm, two aerial robots" nocomm abl_team mixed $seed _AA '{"team": "AA"}' --episodes 80 --team AA
 done ;;
esac
# Added after the team ablation exposed a symmetric livelock of the mutual room-avoidance rule in
# same-type teams: the same teams with a priority rule (only the second robot yields).
if [ "$1" = "team_prio" ]; then
 for seed in 0 1 2 3 4; do
  run ablation "NL, priority rule"                    nl     abl_team mixed $seed _GA_prio '{"team": "GA", "prio": 1}' --episodes 80 --team GA --prio 1
  run ablation "Symbolic, priority rule"              sym    abl_team mixed $seed _GA_prio '{"team": "GA", "prio": 1}' --episodes 80 --team GA --prio 1
  run ablation "Symbolic messaging"                   sym    abl_team mixed $seed _GA '{"team": "GA"}' --episodes 80 --team GA
  run ablation "NL, two ground robots, priority rule" nl     abl_team mixed $seed _GG_prio '{"team": "GG", "prio": 1}' --episodes 80 --team GG --prio 1
  run ablation "NL, two aerial robots, priority rule" nl     abl_team mixed $seed _AA_prio '{"team": "AA", "prio": 1}' --episodes 80 --team AA --prio 1
 done
fi

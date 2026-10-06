#!/bin/bash
# Paired episode-level comparisons (group `paired` and `paired_sweeps`), computed from the per-episode CSVs.
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
PY=${PY:-/Users/pumpkinpies/Donna/Mihir/mihir-s-platform-on-top-his-existing-git/data/envs/sci/bin/python}
pair() {  # name group task tag a b [extra]
  name=$1; group=$2; task=$3; tag=$4; a=$5; b=$6; shift 6
  f=results/raw/${group}_${tag}_${task}.json
  rh run --kind ablation --name "$name" --group $group --task $task --seed 0 --metrics-file $f -- \
    $PY method/analyze.py --a $a --b $b --task $task --seed 0 --out $f "$@" 2>&1 | grep -E "^\[" | cut -c1-200
}
for task in exact synonym attribute relational all; do
  pair "NL minus Symbolic" paired $task nl_sym search_nl search_sym
  pair "NL+coords minus Symbolic" paired $task nlc_sym content_nl_coords search_sym
  pair "Symbolic+attr minus Symbolic" paired $task syma_sym content_sym_attr search_sym
  pair "Symbolic+conf minus Symbolic" paired $task symc_sym content_sym_score search_sym
  pair "NL minus NL+coords" paired $task nl_nlc search_nl content_nl_coords
  pair "Symbolic minus No comm" paired $task sym_nocomm search_sym search_nocomm
  pair "NL minus No comm" paired $task nl_nocomm search_nl search_nocomm
  pair "Oracle minus Symbolic" paired $task oracle_sym search_oracle search_sym
done
# contrast of the pooled difference: (attribute + relational) minus (exact + synonym)
pair "NL minus Symbolic, open minus closed tiers" paired all nl_sym_contrast search_nl search_sym --contrast
pair "NL+coords minus Symbolic, open minus closed tiers" paired all nlc_sym_contrast content_nl_coords search_sym --contrast
pair "Symbolic+attr minus Symbolic, open minus closed tiers" paired all syma_sym_contrast content_sym_attr search_sym --contrast
pair "Symbolic+conf minus Symbolic, open minus closed tiers" paired all symc_sym_contrast content_sym_score search_sym --contrast
pair "NL minus NL+coords, open minus closed tiers" paired all nl_nlc_contrast search_nl content_nl_coords --contrast
pair "Symbolic minus No comm, open minus closed tiers" paired all sym_nocomm_contrast search_sym search_nocomm --contrast
pair "NL minus No comm, open minus closed tiers" paired all nl_nocomm_contrast search_nl search_nocomm --contrast
pair "Oracle minus Symbolic, open minus closed tiers" paired all oracle_sym_contrast search_oracle search_sym --contrast
for v in 0.0 0.1 0.2 0.4; do
  pair "NL minus Symbolic, corruption $v" paired_sweeps mixed corrupt_$v sweep_corrupt_nl_$v sweep_corrupt_sym_$v
done
for v in 0.1 0.2 0.4; do
  pair "Shift of NL minus Symbolic, corruption $v vs 0" paired_sweeps mixed corruptshift_$v sweep_corrupt_nl_$v sweep_corrupt_sym_$v --a2 sweep_corrupt_nl_0.0 --b2 sweep_corrupt_sym_0.0
  pair "NL, corruption $v minus clean"       paired_sweeps mixed nlcorr_$v  sweep_corrupt_nl_$v  sweep_corrupt_nl_0.0
  pair "Symbolic, corruption $v minus clean" paired_sweeps mixed symcorr_$v sweep_corrupt_sym_$v sweep_corrupt_sym_0.0
done
for v in 1 5 10 20; do
  pair "NL minus Symbolic, K=$v" paired_sweeps mixed K_$v sweep_K_nl_$v sweep_K_sym_$v
done
for v in 1 3 5; do
  pair "NL minus Symbolic, resolution $v" paired_sweeps mixed res_$v sweep_res_nl_$v sweep_res_sym_$v
done
for v in 0.0 1.0 2.0; do
  pair "NL minus Symbolic, noise $v" paired_sweeps mixed noise_$v sweep_noise_nl_$v sweep_noise_sym_$v
done

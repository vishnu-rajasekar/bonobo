# M3 Benchmark-Hardened Policy Comparison

Generated after adding `benchmark_complete` and `benchmark_validity` to kernel metrics.

## Batch Summary Paths

- weighted: `experiments/vector_gs_kernel_v1_runs_benchmark_hardened/weighted/20260707_231956_batch_summary.json`
- uniform: `experiments/vector_gs_kernel_v1_runs_benchmark_hardened/uniform/20260707_231956_batch_summary.json`

## Reproducibility Fields

Both batch summaries include:

- `problem_id`: `default_cantilever_v1`
- `policy_id`: `rule_weighted_random_v1` or `rule_uniform_random_v1`
- `seeds`: explicit seed list `0..49`
- `seed_count`: `50`
- `step_budget`: `12`
- per-run `step_budget`: `12`
- aggregate `invalidity_reason_counts`

## Aggregate Metrics

| Metric | Weighted | Uniform |
| --- | ---: | ---: |
| Residual-only completion rate | 0.4400 | 0.5000 |
| Benchmark completion rate | 0.1600 | 0.2600 |
| Benchmark complete runs | 8 | 13 |
| Support-connected runs | 10 | 20 |
| Geometrically valid runs | 40 | 38 |
| Mean residual | 6.6435 | 5.3714 |
| Mean material proxy | 10.6558 | 14.6513 |

## Paired Differences

All differences are `uniform - weighted` over seeds `0..49`.

| Difference metric | Mean | 95% CI | Positive | Negative | Zero |
| --- | ---: | ---: | ---: | ---: | ---: |
| `benchmark_complete` | 0.1000 | [-0.0746, 0.2746] | 12 | 7 | 31 |
| `equilibrium_reached` | 0.0600 | [-0.1503, 0.2703] | 15 | 12 | 23 |
| `support_connected` | 0.2000 | [0.0096, 0.3904] | 17 | 7 | 26 |
| `geometrically_valid` | -0.0400 | [-0.1915, 0.1115] | 6 | 8 | 36 |
| `residual` | -1.2721 | [-4.2460, 1.7018] | 16 | 20 | 14 |
| `material` | 3.9955 | [1.0154, 6.9757] | 35 | 13 | 2 |

## Invalid Geometry Reasons

| Reason | Weighted runs | Uniform runs |
| --- | ---: | ---: |
| `crossing_members` | 6 | 7 |
| `duplicate_members` | 4 | 4 |
| `duplicate_nodes` | 1 | 1 |
| `overlapping_members` | 1 | 0 |

## Interpretation

- `equilibrium_reached` remains residual-only for compatibility.
- `benchmark_complete` is stricter: residual completion, support connectivity, and geometric validity must all be true.
- The rerun confirms the visual concern: many residual-complete runs are not benchmark-complete.
- Uniform remains ahead on support connectivity and benchmark completion for this one problem, but also uses more material on average.

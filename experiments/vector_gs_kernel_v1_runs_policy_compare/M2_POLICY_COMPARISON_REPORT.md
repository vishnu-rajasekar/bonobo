# M2 Policy Comparison Evidence Report

Generated from existing local artifacts. No kernel source code was changed by this report.

## Inputs

- weighted: `experiments/vector_gs_kernel_v1_runs_policy_compare/weighted/20260504_224515_batch_summary.json`
- uniform: `experiments/vector_gs_kernel_v1_runs_policy_compare/uniform/20260504_224525_batch_summary.json`
- Problem: `default_cantilever_v1`
- Seeds: `0..49`, paired across policies
- Expected step budget: `12`; per-run artifacts do not store `step_budget`, so trace length was checked instead

## Integrity

| Policy | Run files | Summary runs | Seeds ok | Problem ok | Policy ok | Trace budget ok | Trace length = accepted steps | Issues |
| --- | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| weighted | 50 | 50 | True | True | True | True | True | 0 |
| uniform | 50 | 50 | True | True | True | True | True | 0 |

## Aggregate Metrics

| Metric | Weighted | Uniform |
| --- | ---: | ---: |
| Residual completion rate | 0.4400 | 0.5000 |
| Structural completion rate | 0.1800 | 0.2800 |
| Support connectivity rate | 0.2000 | 0.4000 |
| Mean accepted steps | 10.7600 | 10.1000 |
| Mean final residual magnitude | 6.6435 | 5.3714 |
| Mean material proxy | 10.6558 | 14.6513 |
| Mean node count | 5.5600 | 5.9200 |
| Mean member count | 3.1200 | 3.6000 |

Structural completion in this report means residual completion plus load-to-support connectivity. This is stricter than the current kernel `equilibrium_reached` metric.

## Paired Differences

All differences are `uniform - weighted` over matched seeds.

| Difference metric | Mean | 95% CI | Positive | Negative | Zero |
| --- | ---: | ---: | ---: | ---: | ---: |
| `completion_delta_uniform_minus_weighted` | 0.0600 | [-0.1503, 0.2703] | 15 | 12 | 23 |
| `structural_completion_delta_uniform_minus_weighted` | 0.1000 | [-0.0746, 0.2746] | 12 | 7 | 31 |
| `support_connected_delta_uniform_minus_weighted` | 0.2000 | [0.0096, 0.3904] | 17 | 7 | 26 |
| `accepted_steps_delta_uniform_minus_weighted` | -0.6600 | [-1.7259, 0.4059] | 14 | 16 | 20 |
| `residual_delta_uniform_minus_weighted` | -1.2721 | [-4.2460, 1.7018] | 16 | 20 | 14 |
| `material_delta_uniform_minus_weighted` | 3.9955 | [1.0154, 6.9757] | 35 | 13 | 2 |
| `node_count_delta_uniform_minus_weighted` | 0.3600 | [-0.1717, 0.8917] | 25 | 13 | 12 |
| `member_count_delta_uniform_minus_weighted` | 0.4800 | [-0.2072, 1.1672] | 22 | 16 | 12 |

## Representative Runs

### weighted

| Category | Seed | Residual complete | Support connected | Residual | Material | Path |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `structural_success_lowest_material` | 0 | True | True | 0.0000 | 12.0000 | `experiments/vector_gs_kernel_v1_runs_policy_compare/weighted/20260504_224515_seed_0/kernel_run.json` |
| `residual_complete_but_not_support_connected_lowest_material` | 14 | True | False | 0.0000 | 2.8445 | `experiments/vector_gs_kernel_v1_runs_policy_compare/weighted/20260504_224515_seed_14/kernel_run.json` |
| `failure_lowest_residual` | 19 | False | True | 1.0000 | 12.0252 | `experiments/vector_gs_kernel_v1_runs_policy_compare/weighted/20260504_224515_seed_19/kernel_run.json` |
| `median_by_residual` | 43 | False | False | 9.5394 | 2.6217 | `experiments/vector_gs_kernel_v1_runs_policy_compare/weighted/20260504_224515_seed_43/kernel_run.json` |

### uniform

| Category | Seed | Residual complete | Support connected | Residual | Material | Path |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `structural_success_lowest_material` | 0 | True | True | 0.0000 | 12.0000 | `experiments/vector_gs_kernel_v1_runs_policy_compare/uniform/20260504_224525_seed_0/kernel_run.json` |
| `residual_complete_but_not_support_connected_lowest_material` | 1 | True | False | 0.0000 | 2.5462 | `experiments/vector_gs_kernel_v1_runs_policy_compare/uniform/20260504_224525_seed_1/kernel_run.json` |
| `failure_lowest_residual` | 16 | False | True | 1.0000 | 12.1019 | `experiments/vector_gs_kernel_v1_runs_policy_compare/uniform/20260504_224525_seed_16/kernel_run.json` |
| `median_by_residual` | 16 | False | True | 1.0000 | 12.1019 | `experiments/vector_gs_kernel_v1_runs_policy_compare/uniform/20260504_224525_seed_16/kernel_run.json` |

## Interpretation

- The artifact set is internally consistent for problem, policy, seed pairing, and trace length budget.
- The current kernel completion metric is residual-only: `final_residual_magnitude <= 1e-9`.
- Under residual-only completion, weighted completes 22/50 and uniform completes 25/50.
- Under stricter structural completion, requiring residual completion and support connectivity, weighted completes 10/50 and uniform completes 20/50.
- The generated structures can therefore look incomplete because many residual-complete runs are not support-connected, and residual cancellation alone is not the same as benchmark-valid structural closure.
- Uniform random currently has better support connectivity and stricter structural completion on this one problem, while weighted random has lower material proxy. This remains single-problem evidence, not a general policy claim.

## Output Artifacts

- Machine-readable paired evidence: `experiments/vector_gs_kernel_v1_runs_policy_compare/m2_policy_comparison_evidence.json`
- This report: `experiments/vector_gs_kernel_v1_runs_policy_compare/M2_POLICY_COMPARISON_REPORT.md`

# SEMANTICS_STRENGTHENING_V1

## Why Step 6 exists
Step 5 produced multi-step, support-connected, plausibility-passing episodes, but they often remained semantically hollow:
- residual stayed flat
- unresolved force stayed stranded on free nodes
- episodes ended by exhausting admissible moves rather than approaching closure

## What Step 6 changed
Two narrow changes were made.

### 1. Direct support link now transfers unresolved force
When `single_node_root_link_rule` connects an active node directly to a fixed support node:
- the edge is added
- the source node `temp_force` is cleared
- the same unresolved force is accumulated onto the support node
- `ReactionAbsorptionChannel` can then absorb it on evaluation

This turns direct support engagement into a semantic event rather than only a graph event.

### 2. Run artifacts now expose semantic progress
The experiment artifacts now record:
- `unresolved_force_magnitude_history`
- `absorbed_magnitude_history`
- `final_unresolved_force_magnitude`

The policy baseline study now aggregates:
- `mean_final_unresolved_force_magnitude`
- `runs_with_residual_improvement`
- `runs_with_unresolved_force_improvement`

## What improved
Residual is no longer universally flat.

Under the Step 6 rerun:
- `random` showed mean final residual `7.27` and residual improvement in `3/5` runs
- `weighted_random` showed mean final residual `8.23` and residual improvement in `2/5` runs
- support-connected runs now show matching drops in unresolved-force magnitude and nonzero absorbed magnitude

Representative semantic-progress run:
- `experiments/runs/20260329_030043_11`
- rule sequence: `split_node_rule -> triangle_closure_rule -> single_node_root_link_rule`
- residual history: `10.0 -> 10.0 -> 10.0 -> 5.4066`
- absorbed magnitude history ends at `5.4066`

## What remains unresolved
The improvement is selective, not universal.

`benchmark_ranked` and `heuristic` still showed:
- no support-path completion in the 5-seed study
- flat residual
- no support absorption events

So the next bottleneck is no longer “support links do nothing semantically.”
It is:
- getting policies and rule realizations to reach semantic support engagement more reliably
- and then resolving the remaining unresolved force after partial absorption

## Current status
Bonobo is closer to honest closure than in Step 5, but not yet at true closure.
The semantics now move when direct support engagement happens; the next step is to make that engagement reachable and complete more consistently.

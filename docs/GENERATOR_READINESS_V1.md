# GENERATOR_READINESS_V1

## Purpose
Record the Step 5 generator-readiness check before any RL work.

## Why This Step Exists
Step 4 showed that the control path was ready but the generator was not:
- `GrammarAction` enumeration worked
- baseline policies worked
- logging and comparison worked
- episodes still stalled at about one accepted step

The bottleneck was generator middle-game continuation, not policy machinery.

## Small Strengthening Moves Made
- `SplitNodeRule` now decomposes unresolved force across branch directions instead of copying the same force to both branches.
- `TriangleClosureRule` now detects shared-parent closure opportunities regardless of node ordering.
- benchmark admissibility now counts closure progress as structural progress when triangle count increases or connected components reduce.
- the provisional `single_node_root_link_rule` is now active in the primary benchmark path and can propose support-link continuation for active fronts with real graph degree.

## Relation To Abstract Grammar
These changes strengthen existing provisional realizations rather than adding new top-level grammar intents.

Relevant intents improved in practice:
- `SplitNode`
- `CloseStructure`
- provisional `ExtendAndConnectTwoNodes`

The vector-GS runtime mapping remains provisional.
The benchmark is still a validator, not the architecture.

## Step 5 Outcome
The generator now exceeds the pre-RL readiness threshold under baseline non-learning policies.

Observed on the primary Michell benchmark over 5 seeds:
- `benchmark_ranked`: mean accepted steps `4.8`, support-path completion `5/5`
- `heuristic`: mean accepted steps `4.8`, support-path completion `5/5`
- `random`: mean accepted steps `5.4`, support-path completion `5/5`
- `weighted_random`: mean accepted steps `3.8`, support-path completion `4/5`

Structural plausibility guardrails remained active:
- no false-positive equilibrium closures were reintroduced
- plausibility pass remained `5/5` across policies

## Remaining Bottleneck
The generator is now alive enough for pre-RL work, but it is not yet closing equilibrium honestly.

Current remaining issues:
- residual stays flat at `10.0`
- global equilibrium remains false
- support paths now exist, but support engagement is ahead of actual force resolution semantics

The next bottleneck is unresolved-force semantics and closure behavior beyond graph connectivity.

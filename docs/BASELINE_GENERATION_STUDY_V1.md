# BASELINE_GENERATION_STUDY_V1

## Purpose
This step evaluates whether Bonobo can generate structurally plausible episodes under baseline non-learning policies before any RL work begins.

The benchmark remains a validator and comparison harness. It does not define the long-term architecture.

## Policies Compared
- `benchmark_ranked`
- `heuristic`
- `random`
- `weighted_random`

These policies all operate over `GrammarAction` through the current policy/control path.

## Metrics That Matter
- accepted step count
- equilibrium / closure count
- support-path existence count
- plausibility-pass count
- termination reason distribution
- invalid-joint rejection frequency
- action / rule diversity
- average node / edge counts
- average support engagement progress

The goal is interpretability and reliability, not statistical overengineering.

## Why This Step Exists
Before RL, the repo needs evidence that:
- admissible `GrammarAction` enumeration is stable
- baseline policies can be compared fairly
- generated episodes are structurally interpretable
- failure modes are visible in logged artifacts

If baseline policies still fail uniformly, the next bottleneck is grammar / semantics rather than learning.

## Outputs
- `experiments/policy_baseline_comparison.json`
- representative runs for viewer inspection
- per-policy aggregate metrics and failure summaries

## What This Prepares
This step prepares Bonobo for a later RL environment by validating:
- policy-facing action control
- action-mask usage
- repeatable episode comparison
- reliability diagnostics over generation behavior

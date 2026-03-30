# POLICY_BASELINES_V1

## Purpose
This document defines the current policy-facing control path after Step 3 of the RL-ready refactor.

The benchmark remains a validator. It does not define the long-term policy architecture.

## GrammarAction As Policy Language
- Policies act over `GrammarAction`.
- `GrammarAction` is the control object that carries:
  - abstract rule id and name
  - method family
  - implementation rule name
  - operator strategy
  - target ids
  - payload
  - topology summary
  - provisional binding metadata

## Action Bundle / Mask
- The experiment loop builds an `ActionBundle` each step.
- `ActionBundle` contains:
  - `actions`
  - `mask`
  - aligned per-action metadata
  - deterministic ordering metadata
- The mask indicates legality / admissibility for each proposed `GrammarAction`.
- Policies select only from admissible actions.

## Policy Selection Contract
- Policies implement:
  - `select_action(observation, action_bundle, reward_spec, rng=None)`
- The policy receives:
  - derived observation
  - admissible-action bundle
  - reward / objective specification
- The policy returns a decision containing the selected `GrammarAction` plus optional scores / weights for logging.

## Baseline Policies
- `RandomPolicy`
  - uniform random choice over admissible actions
- `WeightedRandomPolicy`
  - metadata-biased random choice using explicit rule/operator weights
- `HeuristicPolicy`
  - lightweight score-based choice using benchmark-facing action metadata
- Compatibility names:
  - `benchmark_ranked`
  - `first_candidate`
  - `stochastic_top_band`

These are baseline control policies, not permanent architecture truth.

## Logging
The experiment trace now records:
- policy name
- observation summary
- action bundle summary
- admissible action count and mask
- selected action id and summary
- policy scores / weights when relevant

## Why This Matters
This prepares the repo for later RL or other guidance methods by:
- making `GrammarAction` the native control language
- exposing admissible actions cleanly
- keeping policy selection separate from grammar generation and evaluator logic

Future RL should plug into this path rather than inventing a second action interface.

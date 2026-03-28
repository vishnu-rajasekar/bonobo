# NEXT_STEPS_V1

## Immediate Objective
Implement the smallest benchmark-mode controls needed to judge whether the current Michell-style planar run is admissible, interpretable, and making structural progress under the revised cantilever-style `v1` benchmark contract.

## What Is Already in Place
- layered graph / grammar / evaluator / experiment architecture
- benchmark scenario, run logging, and machine-readable summaries
- structural DNA and trace exports
- geometry descriptors and accepted-graph digests
- viewer/debug tooling for run interpretation

## Exact Next Coding Tasks
- add benchmark admissibility checks for:
  - domain containment
  - crossing-free accepted graph
  - duplicate node rejection
  - duplicate edge rejection
- add support-distance or support-connectivity diagnostics for accepted states
- log explicit rejection reasons whenever a candidate fails benchmark admissibility or ranking discipline
- add benchmark-mode candidate acceptance or ranking discipline so accepted steps are not arbitrary when multiple candidates exist
- rerun the revised canonical cantilever-style benchmark and compare the result against the prior baseline

## Expected Outputs After Implementation
- compact summary JSON
- structural DNA / rule sequence
- residual history
- support-distance or support-connectivity trend if implemented
- root-region distance or root-connectivity trend if the diagnostics are still node-based approximations
- accepted graph digest with coordinates and edges
- 5 to 10 iteration records showing accepted or rejected decisions and reasons

## What Not to Build Yet
- 3D extensions
- curved-surface conformance
- scaffold-free shell logic
- typology diversity objectives in code
- learned guidance, reinforcement learning, archive systems, or latent-space machinery
- advanced viewer UI
- broad new grammar families unless benchmark evidence clearly justifies one minimal addition

## Decision Points After the Next Benchmark Run
- Is the current LOA / `temp_force` / state-machine behavior sufficient to produce admissible, interpretable progress under the `v1` benchmark?
- Are accepted steps moving residuals, unresolved-force burden, or root-region connectivity in the right direction?
- Is the run still dominated by arbitrary first-choice acceptance with little evidence of closure tendency?
- If the current behavior remains non-closing or structurally uninformative, is one minimal new closure-oriented rule justified?
- If a new rule is needed, can it be added as a narrow benchmark-specific closure aid without changing the canonical semantic layers?

## Interpretation Note
For the revised cantilever-style benchmark, support-seeking diagnostics may need to be interpreted as distance or connectivity to a support boundary/root region rather than only nearest support node. If the implementation still uses discrete support-node approximations, that approximation should remain explicit in reporting.

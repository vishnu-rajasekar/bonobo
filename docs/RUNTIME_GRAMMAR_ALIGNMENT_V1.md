# RUNTIME_GRAMMAR_ALIGNMENT_V1

## Benchmark Role
- The current benchmark is a validator and regression check.
- It is not the definition of Bonobo's long-term grammar.
- Runtime mappings that happen to support the benchmark must not be mistaken for final grammar truth.

## Abstract Rules vs Vector GS Realizations
- Abstract grammar rules are frozen in `morph_engine/morph_engine/grammar/abstract_rules.py`.
- Vector GS is the current method-specific realization layer.
- Current runtime bindings live in `morph_engine/morph_engine/grammar/vector_gs/rules.py`.
- Those bindings are explicitly marked `provisional`.

## Current Provisional Mappings
- `ExtendNodeRule` -> `extend_node_rule`
- `SplitNodeRule` -> `split_node_rule`
- `ConnectTwoNodesRule` -> `resolve_two_forces_rule`
- `ExtendAndConnectTwoNodesRule` -> `single_node_root_link_rule`
- `CloseStructureRule` -> `triangle_closure_rule`

These are current runtime realizations, not claims that the mapping is final.

## Operators vs Rules
The following legacy `*_rule.py` modules are treated as vector GS operators or strategy shims rather than additions to the abstract grammar vocabulary:
- `loa_intersection_rule`
- `resolve_temp_force_v1`
- closest projection / closest link helpers in the operator layer
- node equilibration and force-transfer helpers in the operator layer

## GrammarAction Runtime Path
- `GrammarEngine.propose_actions(...)` now exposes applicable actions directly as `GrammarAction`.
- `GrammarEngine.propose(...)` remains as a compatibility path returning legacy concrete proposals.
- `GrammarAction` carries:
  - abstract rule id and name
  - method family
  - implementation rule name
  - operator strategy
  - target ids
  - payload
  - topology summary
  - provisional binding metadata

## What Remains For Later Steps
- move more runtime selection and logging code to consume `GrammarAction` natively
- reduce reliance on legacy `Candidate` terminology
- decide which provisional runtime strategy shims should remain as method realizations and which should be demoted further into operator-only status
- add future GS backends without changing the frozen abstract grammar or policy-facing schemas

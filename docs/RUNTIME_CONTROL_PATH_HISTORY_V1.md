# RUNTIME_CONTROL_PATH_HISTORY_V1

Status: transitional/reference

## Purpose
This document consolidates the main historical runtime documents that described Bonobo's control path before the project shifted to the standalone `vector_gs_kernel_v1` MVP path.

It preserves the runtime-side design record for:
- benchmark-mode next steps
- GS operator grouping
- frozen abstract rule and policy-facing interfaces
- runtime grammar alignment
- baseline non-learning policy behavior

This is useful for long-term reintegration work, but it is not the active MVP implementation guide.

## Scope
This note summarizes and supersedes the following runtime-history docs:
- `docs/NEXT_STEPS_V1.md`
- `docs/GENERATION_CORE_V1.md`
- `docs/RL_INTERFACE_FREEZE_V1.md`
- `docs/RUNTIME_GRAMMAR_ALIGNMENT_V1.md`
- `docs/POLICY_BASELINES_V1.md`
- `docs/BASELINE_GENERATION_STUDY_V1.md`

## 1. Benchmark-Mode Runtime Focus
The original runtime development path centered on a Michell-style planar benchmark used as:
- a validator
- a regression check
- a proving ground for support-seeking, equilibrium-informed growth

That path emphasized:
- admissibility checks
- compact run summaries
- interpretable rule sequences
- traceability of accepted and rejected choices

This benchmark focus remains historically important, but it is no longer the active MVP instruction set.

## 2. Generation Core Structure
The runtime generation core was organized around:
- canonical graph state
- thin grammar rules
- reusable GS operators
- separate evaluator channels
- experiment-owned logging and acceptance logic

The runtime GS operator grouping included:
- force helpers such as `get_temp_force`, `flip_temp_force_dir`, `get_line_of_action`, `transfer_member_force`
- node helpers such as `rearrange_forces`, `equilibrate_node`, `temp_node_equilibrium`, connection and closure search
- member helpers for node/member lookup and force metadata access

This separation remains conceptually relevant for future reintegration.

## 3. Frozen Runtime Interface Vocabulary
The original runtime froze a policy-facing interface around:
- canonical graph `state`
- abstract grammar `rule` intents
- concrete applicable `action`s
- GS `operator` or transformation details
- derived `observation`
- `reward spec`
- `policy`
- `episode`
- `step`

Frozen abstract rule intents:
- `StartGenerationRule`
- `CreateNodeRule`
- `ExtendNodeRule`
- `SplitNodeRule`
- `ConnectTwoNodesRule`
- `ExtendAndConnectTwoNodesRule`
- `CloseStructureRule`
- `EndGenerationRule`

These remain useful as long-term architectural guidance even though the kernel MVP is not currently wired through this interface.

## 4. Runtime Grammar Alignment
The runtime later aligned proposal and application flow around `GrammarAction`.

Important alignment conclusions:
- `GrammarAction` became the policy/control object
- abstract grammar rules remained distinct from GS operators
- vector GS was treated as the current method-specific realization layer
- many legacy `*_rule.py` files were reinterpreted as operator-backed shims rather than true top-level grammar rules

This alignment is still relevant for future adapters from kernel traces into Bonobo runtime concepts.

## 5. Runtime Policy Control Path
The runtime policy/control path introduced:
- `ActionBundle`
- admissibility masks
- deterministic proposal ordering
- policy decision summaries
- per-step logging of selected and admissible actions

Baseline runtime policies included:
- `RandomPolicy`
- `WeightedRandomPolicy`
- `HeuristicPolicy`
- compatibility names such as `benchmark_ranked`

These are historical runtime policies, not the current kernel MVP policy surface.

## 6. Runtime Baseline Study Outcome
The runtime baseline study used non-learning policy comparison to test whether:
- admissible action enumeration was stable
- policies could be compared fairly
- runs were structurally interpretable
- failure modes were visible in artifacts

That work showed that:
- the control path became inspectable and policy-ready
- but the generator itself still had structural-semantic bottlenecks

This was one of the key reasons the project moved toward the standalone kernel MVP.

## 7. Why This Still Matters
This runtime history should be preserved because it records:
- the long-term action-language design
- the separation between grammar, GS operators, evaluator, and experiment harness
- the intended future bridge between an active generator and a structured runtime architecture

It should be read as historical runtime reference, not as the active implementation center.

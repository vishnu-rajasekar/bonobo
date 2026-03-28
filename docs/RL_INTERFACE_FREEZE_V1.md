# RL_INTERFACE_FREEZE_V1

## Core Vocabulary
- `state`: canonical structural state in `StructuralGraph`
- `rule`: abstract grammar intent such as `ExtendNodeRule`
- `action`: one concrete applicable grammar action
- `operator` / `transformation`: GS-method-specific structural-geometric implementation detail
- `observation`: policy-facing derived state view
- `reward spec`: objective and constraint schema for future guidance
- `policy`: chooses among applicable grammar actions
- `episode`: one full generation run
- `step`: one accepted action

## Frozen Abstract Grammar Rules
- `StartGenerationRule`
- `CreateNodeRule`
- `ExtendNodeRule`
- `SplitNodeRule`
- `ConnectTwoNodesRule`
- `ExtendAndConnectTwoNodesRule`
- `CloseStructureRule`
- `EndGenerationRule`

These are the stable top-level rule intents. They are not the same thing as vector GS operators.

## Vector GS Mapping
- Vector GS is the current method-specific backend.
- Current active mappings live in:
  - `morph_engine/morph_engine/grammar/vector_gs/rules.py`
  - `morph_engine/morph_engine/grammar/vector_gs/operators.py`
- The mapping registry covers all frozen abstract rule intents, including interface-only or not-yet-realized entries such as `StartGenerationRule`, `CreateNodeRule`, and `EndGenerationRule`.
- All current abstract-rule to vector-GS runtime bindings are intentionally marked `provisional`.
- Current files such as `loa_intersection_rule`, `resolve_temp_force_v1`, closest-projection/link helpers, and node equilibration helpers should be interpreted as vector GS operators or strategies, not as additions to the frozen abstract rule vocabulary.
- Benchmark-specific rules such as `single_node_root_link_rule` remain provisional shims.

## Policy Observation Schema
- Global features:
  - phase
  - node/edge/support/load counts
  - active front count
  - unresolved-force count
  - support connectivity summary hook
  - plausibility summary hook
- Node features:
  - node id
  - coordinates
  - node kind
  - degree
  - active/open flag
  - temp-force proxy
  - load/support flags
- Edge features:
  - edge id
  - endpoints
  - length
  - direction
  - member kind
  - future force placeholder
- Action mask hook:
  - list of admissible action ids

## Action Schema
- `GrammarAction` freezes:
  - `action_id`
  - `abstract_rule_id`
  - `abstract_rule_name`
  - `method_family`
  - `implementation_rule_name`
  - `target_node_ids`
  - `target_edge_ids`
  - `operator_strategy`
  - `parameter_payload`
  - `topology_delta`
  - `metadata`

## Reward Schema
- `RewardSpec` freezes:
  - `objective_weights`
  - `hard_constraints`
  - `prompt_tags`
  - `benchmark_mode`
  - `phase_bias`

Standard objective keys to keep stable now:
- `residual_reduction`
- `support_engagement`
- `closure_progress`
- `plausibility_pass`
- `member_count_penalty`
- `total_length_penalty`
- `branching_preference`
- `symmetry_preference`
- `domain_constraint_satisfaction`

## Future Extensibility
- Polyhedral GS can later add a parallel method realization layer.
- Airy / stress-based GS can later add another method realization layer.
- RL or other guidance methods should plug into the frozen action, observation, and reward interfaces rather than redefining grammar or state.

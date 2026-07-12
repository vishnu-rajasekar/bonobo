# Bonobo Roadmap

## Purpose

This roadmap orders Bonobo's work from the current vector graphic statics kernel
MVP to the long-term layered runtime. Each milestone has an evidence-based exit
gate. Later milestones should not begin because an earlier prototype merely
runs; they begin when the earlier milestone's artifacts, semantics, and tests
are credible.

## Strategic Direction

The near-term research claim is deliberately narrow:

> A semantically rich vector graphic statics generator can produce
> interpretable sequential structural growth for bounded planar problems,
> preserve machine-readable traces, and support reproducible comparison across
> simple seeded policies.

The active implementation nucleus is
`morph_engine/morph_engine/vector_gs_kernel_v1`. The long-term architecture
remains:

`StructuralGraph -> Grammar -> GS realization -> Evaluator -> Policy -> Experiment Harness`

The kernel is a proving ground, not a replacement for that architecture.

## Status Legend

- **Established**: implemented and retained as project foundation.
- **Active**: current work and the default destination for new effort.
- **Next**: starts after the active milestone passes its exit gate.
- **Later**: intentionally deferred.

## M0 — Layered Runtime Foundation

**Status: Established**

Delivered:

- `StructuralGraph` as canonical runtime state.
- Frozen abstract grammar vocabulary and `GrammarAction`.
- Evaluator channel contracts.
- Seeded experiment and trace infrastructure.
- Tests around loads, supports, `temp_force`, reactions, grammar, and evaluator
  behavior.

Preserve this runtime while kernel validation proceeds. Do not reshape it around
temporary benchmark or kernel implementation details.

## M1 — Vector GS Kernel MVP

**Status: Established**

Delivered:

- Standalone `Assembly`, `Node`, `Force`, and `Member` objects.
- Core vector-GS operators and top-level rule intents.
- Seedable generation loop.
- Explicit `michell_three_point_cantilever_v1` problem.
- Per-run JSON artifacts with assembly, trace, and final metrics.
- Weighted-random and uniform-random rule-selection policies.

Known semantic gaps:

- Support and reaction behavior needs stronger definition and validation.
- Close-system behavior is incomplete across scenarios.
- Some connect operations have provisional force-sign handling.
- GDGS force head/tail and global force-polygon conventions are documented as
  targets but not yet fully enforced.
- Reactions are not yet initialized from applied loads and support directions
  before generation.
- Kernel and layered-runtime semantics currently overlap without adapters.

Exit gate:

- Kernel smoke, semantic, reproducibility, export, and policy-selection tests
  pass.
- Every supported policy can be selected explicitly and reproduces a run for a
  fixed seed.
- Run artifacts contain problem ID, policy ID, seed, trace, assembly, and final
  metrics.

## M2 — First Policy Comparison

**Status: Active**

Executed locally:

- Problem: `default_cantilever_v1`.
- Policies: `rule_weighted_random_v1` and `rule_uniform_random_v1`.
- Seeds: `0..49`, paired across policies.
- Budget: `12` steps per run.
- Output: 50-run batch summaries and 100 per-run artifacts.

Current aggregate evidence:

| Metric | Weighted random | Uniform random |
| --- | ---: | ---: |
| Completion rate | 0.44 | 0.50 |
| Mean accepted steps | 10.76 | 10.10 |
| Mean final residual magnitude | 6.64 | 5.37 |
| Mean material proxy | 10.66 | 14.65 |
| Support-connected runs | 10/50 | 20/50 |

Interpretation remains provisional. Uniform random currently performs better on
completion, residual, and support connectivity, while weighted random uses less
total member length. Aggregate means alone do not establish policy superiority.

Remaining work:

- Validate that all artifacts use the intended problem, policy, seed, and step
  budget.
- Report paired seed-level differences, dispersion, and confidence intervals.
- Define how incomplete runs are handled in each metric.
- Select successful, median, and failed representative runs using explicit,
  reproducible criteria.
- Inspect representative traces in the viewer and record semantic anomalies.
- Capture the exact command, environment, test output, Git revision, and
  worktree state used for the study.
- Decide which generated artifacts are retained as durable evidence rather than
  committing an undifferentiated run dump.

Exit gate:

- A reproducible comparison report links batch summaries to representative run
  artifacts.
- Paired analysis supports every quantitative statement.
- Metrics and failure handling are documented.
- Relevant kernel tests pass from a clean, identified revision.
- No claim exceeds the single-problem, two-policy evidence.

## M3A — GDGS-to-VectorGS Parity Slice

**Status: Active**

Objective: use GDGS as the behavioural reference while retaining VectorGS as the maintained headless implementation.

Work:

- Preserve seeded policies, artifacts, tests, and COMPAS Viewer support.
- Port one complete minimal path covering boundary-force initialization,
  temporary-force propagation, state-derived applicability, and closure.
- Do not add guidance or RL during this milestone.
- Define `michell_three_point_cantilever_v1` explicitly against
  `docs/BENCHMARK_MITCHELL_V1.md`, including geometry, load, support/root
  approximation, bounds, and the 12-step budget.
- Strengthen support-seeking, support connectivity, reaction, residual, and
  equilibrium-completion semantics.
- Enforce one GDGS-compatible force convention: stored force vectors are
  tail-to-head, and force polygons are assembled head-to-tail.
- Add reaction-first global equilibrium setup: derive or solve support reaction
  vectors from authored applied loads plus support reaction directions, then
  require external force-polygon closure before claiming global equilibrium.
- Treat reaction directions and reaction-angle ranges as versioned
  problem/benchmark parameters.
- Resolve or explicitly bound force-sign behavior in connect operations.
- Improve close-system behavior without adding benchmark-only grammar rules.
- Record accepted and rejected actions with machine-readable rejection reasons.
- Enforce or diagnose domain bounds, crossings, duplicate nodes, and duplicate
  members.
- Add focused regression tests for each semantic decision.

Exit gate:

- Benchmark success and failure can be determined from artifacts without viewer
  interpretation.
- Residual, completion, connectivity, and material metrics have stable,
  test-backed meanings.
- Artifact schemas expose the applied loads, solved/initialized reactions,
  reaction directions, and force-polygon residual used for global equilibrium.
- Known semantic approximations are explicit in code-facing documentation.
- Fixed-seed regression cases cover successful closure and representative
  failure modes.

## M3B — Feasibility-Aware Proposal Filtering

**Status: Next**

Apply definite-invalidity filters before policy selection. Initial filters may cover design-domain containment, prohibited intersections, member-length limits, node-angle limits, and rectangle, box, or surface compliance. Record masks and rejection reasons without embedding soft policy preferences in the grammar.

## M3C — Heuristic Guidance Baseline

**Status: Later**

Add one interpretable proposal-ranking policy using a bounded set of criteria such as load-path proxy, domain clearance, mechanism diagnostics, node constructability, and compression-member length or slenderness proxy.

## M3D — Tabular RL Guidance Comparison

**Status: Later**

Compare a minimal interpretable tabular Q-learning or equivalent policy through the same applicable-action interface. Do not introduce GNNs, deep RL, actor-critic methods, continuous learned geometry generation, or LLM control.

## M3E — Held-Out Policy Study and Paper Figures

**Status: Later**

Separate training and evaluation seeds. Report feasible completion, material/load-path performance, dead-end rate, generation steps, diversity, constraint-mask statistics, and generalisation to controlled boundary-condition changes.

## M4 — Compact Benchmark Family

**Status: Next**

Objective: test whether observed behavior survives small, controlled problem
changes.

Work:

- Retain the canonical cantilever case as the primary benchmark.
- Add no more than one or two directly comparable variations, such as load
  position, load magnitude/direction, or root/support geometry.
- Give every problem a versioned ID and fully serialized definition.
- Run matched seeds and identical budgets across policies and problems.
- Add a diversity measure that distinguishes genuinely different assemblies
  from seed-level noise.
- Introduce a lightweight greedy or heuristic policy only if it expresses a
  clear structural hypothesis and requires no new action language.

Exit gate:

- Every benchmark is small, reproducible, and visually inspectable.
- Cross-problem reporting separates robust trends from case-specific effects.
- The problem family is sufficient for the paper claim without implying broad
  typological coverage.

## M5 — Paper Evidence Package

**Status: Later, after M2-M4**

Work:

- Freeze experiment configuration, metric definitions, and artifact schema.
- Produce a sequential growth figure and representative rule examples.
- Produce policy comparison tables with uncertainty, not means alone.
- Show multiple valid alternatives for the same problem.
- Include failure cases and semantic limitations.
- Package commands, environment information, retained artifacts, and figure
  generation steps for reproducibility.

Exit gate:

- Every table and figure is regenerable from retained machine-readable
  artifacts.
- The evidence supports the narrow research claim in this roadmap.
- Non-claims remain explicit: no structural optimality, universal equilibrium,
  broad typology, construction intelligence, or learned-policy superiority.

## M6 — Adapter-Based Reintegration

**Status: Later**

Start only after the kernel's objects, traces, and metrics are stable enough to
map without semantic guesswork.

Work:

- Map kernel `Assembly` data into `StructuralGraph`.
- Map kernel rule traces into `GrammarAction` and experiment trace concepts.
- Map kernel diagnostics into evaluator channel outputs.
- Keep kernel objects from becoming a second canonical runtime state.
- Port incrementally behind adapters with equivalence and round-trip tests.
- Reuse the layered experiment harness rather than duplicating it.

Exit gate:

- One benchmark can run through the adapter-backed layered path with equivalent
  accepted geometry, trace intent, and metrics.
- Canonical ownership of every field is documented.
- Kernel-specific code can remain isolated or be retired without breaking the
  public action and experiment contracts.

## M7 — Domain and Typology Expansion

**Status: Later**

Possible directions:

- Bounded-volume and keep-out constraints.
- Curved-surface conformance.
- Additional static schemes such as branching compression systems, cable nets,
  gridshells, and shells.
- Alternative GS realizations such as polyhedral or Airy/stress-field methods.

Each extension requires its own problem contract, validity checks, metrics, and
regression fixtures. Do not generalize from the planar cantilever by changing
its semantics in place.

## M8 — Guidance and Learning

**Status: Later**

Prerequisites:

- Stable abstract action language.
- Admissible-action enumeration and masks.
- Stable derived observation and reward schemas.
- Credible benchmark family and non-learning baselines.
- Reproducible artifacts suitable for training and evaluation.

Initial learned components should rank or suggest admissible grammar actions.
They must not introduce a second action language or replace canonical structural
state with derived arrays. Reinforcement learning is not a near-term coding
step.

## M9 — Construction-Aware Growth

**Status: Later**

Investigate staged stability, fabrication constraints, assembly sequencing, and
scaffold-free growth only after generator semantics, benchmark evidence, and
runtime reintegration are credible. These goals require new evaluator contracts
and should remain separate from the first paper claim.

## Decision Rules

- Semantic changes to loads, supports, reactions, `temp_force`, or completion
  require explicit review and focused tests.
- Benchmark logic validates the generator; it does not define the abstract
  grammar.
- Viewer output is interpretive. Engine artifacts remain the source of truth.
- New policies must select from existing admissible actions.
- New metrics require a definition, failure-handling rule, and artifact field
  before they are used in claims.
- A milestone is complete only when its exit gate is met and evidenced, not when
  its implementation first runs.
- Milestone completion does not imply automatic GitHub publication. After an
  exit gate is met, report changed files, test output, `git status --short`, and
  `git diff --stat`; commit and push only after explicit user approval.

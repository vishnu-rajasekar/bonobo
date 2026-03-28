# BENCHMARK_MITCHELL_V1

## Purpose
Define one canonical Michell-style planar benchmark for near-term validation of Bonobo's equilibrium-informed growth workflow.

For `v1`, the primary Michell-style reference is a cantilever-style boundary-value problem. The previous two-support central-load case remains useful as a secondary planar sanity benchmark, but it is not the primary Michell-style benchmark.

## Scope
- 2D planar benchmark only
- single cantilever-style boundary-value problem
- sequential growth under the current layered Bonobo architecture
- benchmark interpretation only; broader typologies and later-stage ambitions are out of scope for `v1`

## Canonical Geometry
- support-side/root condition on the left side of the domain
- benchmark support region centered on `x = -5`
- load point at `(5, 2)`
- planar embedding in XY

## Supports and Support-Side Condition
- primary benchmark interpretation:
  - the left/root side acts as the cantilever support condition
  - growth should be interpreted relative to connectivity and approach toward that support boundary/root region
- current implementation note:
  - the present experiment layer does not yet express a continuous support boundary cleanly
  - `v1` therefore approximates the cantilever root with two fixed support nodes on the left side
  - this is an explicit approximation, not a claim that the current code already models a true continuous cantilever root

## Load Definition
- one downward point load
- canonical load vector: `(0, -10)`
- load is applied at `(5, 2)`
- no additional load cases are part of `v1`

## Domain Bounds
- rectangular benchmark domain
- `x in [-6, 6]`
- `y in [-1, 6]`

## Iteration Budget
- canonical provisional budget: `12` accepted iterations
- this budget remains intentionally bounded so traces stay inspectable and comparisons remain simple
- if changed later, the change should be treated as a benchmark revision rather than a silent parameter tweak

## Immediate Benchmark Goal
Generate materially efficient, equilibrium-seeking emergent structure for this Michell-style cantilever problem while keeping the growth process traceable and geometrically admissible.

## Admissibility Conditions
At benchmark level, an accepted step should satisfy all of the following:
- accepted structure remains inside domain bounds
- accepted graph is crossing-free
- duplicate nodes are invalid
- duplicate edges are invalid
- accepted steps should not worsen the chosen structural progress measure
- intermediate states must remain structurally meaningful under the current benchmark interpretation

For `v1`, "structurally meaningful" means:
- the accepted graph still represents a coherent load-root problem
- accepted geometry is not obviously degenerate under the current descriptor checks
- the step can be explained by recorded trace outputs

## Success Criteria
A benchmark run is a `v1` success candidate when the outputs show all of the following:
- canonical cantilever-style geometry, load, and iteration budget were used
- accepted graph remains inside bounds
- accepted graph is crossing-free
- duplicate node count is `0`
- duplicate edge count is `0`
- trace outputs clearly show accepted and explored geometry
- rule sequence and run summary are machine-readable
- the chosen structural progress measure is stable or improves over the run
- growth shows interpretable approach or connectivity tendency toward the left/root support side
- residual behavior and unresolved-force burden can be inspected directly from run artifacts

## Failure Criteria
A benchmark run is a `v1` failure candidate when any of the following occurs:
- accepted graph leaves the benchmark domain
- accepted graph contains crossings
- duplicate nodes or duplicate edges appear
- trace outputs are insufficient to explain accepted decisions
- accepted steps worsen the recorded structural progress measure without an explicit logged reason
- the run produces no interpretable evidence of equilibrium-seeking or support-directed behavior toward the root region

## Secondary Sanity Benchmark
The previous two-support central-load planar case remains useful as a secondary sanity benchmark because it is simple, inspectable, and exercises the same logging/ranking infrastructure. It should be retained where already available, but it should no longer be treated as the primary Michell-style reference problem.

## Outputs to Inspect
- compact summary JSON
- per-iteration trace
- rule sequence / structural DNA
- residual history
- accepted graph digest with coordinates and edges
- geometry validity descriptors
- support-distance or support-connectivity diagnostics, interpreted relative to the root region approximation
- rejection reasons when implemented

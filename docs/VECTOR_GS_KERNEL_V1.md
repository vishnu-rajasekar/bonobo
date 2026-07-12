# Vector GS Kernel V1

## What this is
`vector_gs_kernel_v1` is a standalone, semantically rich vector graphic statics kernel built as the shortest path to a working GDGS-like generator before reintegration into the main Bonobo runtime.

It is intentionally more direct than the current Bonobo architecture:
- real kernel objects for `Assembly`, `Node`, `Force`, and `Member`
- Juney-inspired local force-list semantics
- compact operator library
- Juney-style top-level generative rules
- a small random generation loop

## Why it exists
The current Bonobo runtime was accumulating too much adaptation overhead while still not behaving like a rich GDGS-style vector engine. This kernel is a tactical reset:
- recover Juney-like semantics quickly
- make the generator inspectable
- validate generation behavior first
- integrate back later

## Main inspirations from `GDGS`
- local node force lists
- temporary force driven line of action
- member-force transfer between nodes
- force vectors interpreted tail-to-head, with force polygons assembled
  head-to-tail
- applied loads and support reactions treated as upfront boundary forces whose
  external force polygon must close before generation claims global equilibrium
- `CreateNode`, `ExtendNode`, `SplitNode`, connection, projection, and close-system rule ideas
- weighted random rule application over active nodes

## How it differs from the main Bonobo runtime
- it is standalone
- it is not wired into `GrammarAction`, policy baselines, or benchmark harnesses
- it uses direct kernel objects instead of the graph-first runtime
- it optimizes for working vector-GS generation first, not architecture integration

## How to run it
From the repo root:

```bash
python scripts/run_vector_gs_kernel_v1.py --runs 3 --steps 12
```

Artifacts are written to:

```text
experiments/vector_gs_kernel_v1_runs/
```

Each run writes a `kernel_run.json` containing:
- final assembly state
- nodes
- members
- forces
- step trace

## Current scope
Implemented kernel pieces:
- semantic objects
- core force/node/member operators
- all top-level rule intents
- compact generation loop
- seedable runner

Still missing before reintegration:
- GDGS-style support/reaction semantics: derive reaction vectors from applied
  loads and support reaction directions, then verify external force-polygon
  closure
- richer close-system behavior across more scenarios
- more faithful force-sign handling in some connect cases
- a viewer adapter for kernel runs

## Force convention target
The kernel should use one force convention everywhere: vectors point from tail
to head in the stored vector direction, and force polygons are checked by placing
vectors head-to-tail. For global equilibrium, authored loads plus solved support
reactions must sum to zero within tolerance. For local equilibrium, member,
load, and reaction forces at a node should close under the same convention.

Until this is implemented completely, artifacts and reports must not imply
GDGS-equivalent equilibrium merely because residual metrics are small.

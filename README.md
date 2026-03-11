# Bonobo

Bonobo is a layered structural generation engine for the guided emergence of structural form through sequential, equilibrium-informed growth under geometric and construction constraints.

The project is organized around explicit layers:
- `StructuralGraph` as canonical state
- grammar rules and engine for admissible growth actions
- evaluator channels for structural signals and validity checks
- experiment harnesses for benchmark scenarios, traces, descriptors, and derived exports

Bonobo is not currently presented as a general search platform or learned design-space engine. The immediate proof target is a 2D Michell-style planar benchmark in which growth remains interpretable, benchmarked, and tied to equilibrium-related signals.

## Current Focus
- Benchmark validation before learning, search expansion, or large-scale diversity machinery
- Equilibrium-informed, support-seeking growth on a Michell-style planar problem
- Admissible intermediate states, not only final-state evaluation
- Machine-readable traces, descriptors, and summaries that explain what the generator actually did
- Material efficiency as the first benchmark performance goal

## Longer-Term Direction
- Goal steering and diversity across multiple valid solutions to the same problem
- Broader static schemes such as truss, branching compression systems, tensegrity, cable-net, gridshell, and shells
- Construction-aware growth including staged stability, scaffold-free growth, and curved-surface conformance
- Learned guidance, latent-space structure, and policy support only after benchmark grounding is credible

## Repository Map
- `morph_engine/`: core package and unit tests
- `morph-rhino-mcp/`: Rhino MCP server integration
- `scripts/`: experiments and runnable demos
- `research/`: source reference material
- `docs/`: supporting architecture and governance notes
- `experiments/`: benchmark configs, traces, and run outputs
- `integration_tests/`: reserved for Rhino/MCP integration tests

## Quick Check
Run unit tests from the repository root:

```bash
conda run -n morph-engine python -m pytest
```

Run the current benchmark entrypoint:

```bash
conda run -n morph-engine python scripts/run_experiment.py
```

## Conda Env
```bash
conda env remove -n morph-engine
conda env create -f morph_engine/environment.yml
conda activate morph-engine
pip install -e ./morph_engine
```

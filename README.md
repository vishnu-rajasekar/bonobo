# Bonobo

Bonobo is a layered structural generation engine for the guided emergence of structural form through sequential, equilibrium-informed growth under geometric and construction constraints.

The project is organized around explicit layers:
- `StructuralGraph` as canonical state
- grammar rules and engine for admissible growth actions
- evaluator channels for structural signals and validity checks
- experiment harnesses for benchmark scenarios, traces, descriptors, and derived exports

Bonobo is not currently presented as a general search platform or learned design-space engine. The long-term architectural target remains the layered Bonobo runtime, but the current MVP implementation path is kernel-first:
- active technical nucleus: `morph_engine/morph_engine/vector_gs_kernel_v1`
- long-term reintegration target: the layered Bonobo runtime centered on `StructuralGraph`, grammar, evaluator, and experiments
- future bridge: adapters between kernel assemblies, traces, and metrics and Bonobo runtime concepts

The immediate proof target is a compact, inspectable vector graphic statics generator that preserves the useful state and rule mechanics of GDGS and supports policy-independent guidance studies through seeded runs.

## Current Focus
- Stabilize and evaluate `vector_gs_kernel_v1` through reproducible seeded experiments
- Preserve the layered Bonobo runtime as the long-term architectural target
- Keep kernel artifacts, traces, and viewers inspectable and machine-readable
- Use small benchmark/problem definitions to validate generation behavior without overclaiming general structural design capability
- Establish controlled GDGS-to-VectorGS behavioural parity before adding guidance
- Keep engine invariants separate from policy guidance and evaluation criteria

## Longer-Term Direction
- Adapter-based reintegration of the kernel into the layered Bonobo runtime
- Goal steering and diversity across multiple valid solutions to the same problem
- Broader static schemes such as truss, branching compression systems, cable-net, gridshell, and shells
- Construction-aware growth and richer domain handling only after the generator core is credible
- Learned guidance and policy support only after benchmark grounding and kernel evaluation are credible

GDGS supplies the behavioural reference for equilibrium-aware grammar mechanics. VectorGS remains the maintained headless runtime. Engine correctness covers force closure, temporary-force propagation, member action-reaction behaviour, force/member collinearity, and valid state transitions. Guidance evaluates otherwise applicable actions using feasibility, efficiency, stability, constructability, architectural, fabrication, and diversity criteria.

## Repository Map
- `morph_engine/`: core package and unit tests
- `morph_engine/morph_engine/vector_gs_kernel_v1/`: active standalone vector GS kernel MVP
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

Run the current kernel MVP entrypoint:

```bash
python scripts/run_vector_gs_kernel_v1.py --runs 3 --steps 12
```

Run the current layered-runtime benchmark entrypoint:

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

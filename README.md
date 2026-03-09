# Bonobo

Bonobo is a structural grammar research engine evolving toward production-grade tooling.

## Repository Map
- `morph_engine/`: core package and unit tests
- `morph-rhino-mcp/`: Rhino MCP server integration
- `scripts/`: experiments and runnable demos
- `research/`: source reference material
- `docs/`: architecture and governance documentation
- `experiments/`: experiment configs and run outputs
- `integration_tests/`: reserved for Rhino/MCP integration tests

## Quick Check
Run unit tests from repository root:

```bash
pytest
```

## Conda env
conda env remove -n morph-engine
conda env create -f environment.yml
conda activate morph-engine
pip install -e ./morph_engine
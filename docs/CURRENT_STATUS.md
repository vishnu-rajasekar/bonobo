# Current Status — Bonobo

## Active MVP Path
`vector_gs_kernel_v1`

The active paper-facing implementation path is the standalone vector GS kernel in:
- `morph_engine/morph_engine/vector_gs_kernel_v1`

## Long-Term Architecture
Layered Bonobo runtime:
- `StructuralGraph`
- Grammar
- Evaluator
- Experiment Harness

The kernel is not a replacement for this architecture. It is the current implementation nucleus for proving the generator before reintegration.

## Current Decision
The vector GS kernel is the active MVP technical nucleus for the first conference-paper-oriented implementation.

The original Bonobo runtime remains:
- preserved
- testable
- architecturally important
- the intended reintegration target later

## Current Non-Goals
- full runtime reintegration
- LLM interface work
- GNN guidance
- deep RL
- construction staging
- polyhedral GS implementation
- Airy/stress-field backend implementation

## Current Runnable Entrypoints
- kernel runs:
  - `python scripts/run_vector_gs_kernel_v1.py --runs 3 --steps 12`
- kernel viewer:
  - `python scripts/view_vector_gs_kernel_run.py`
- original runtime benchmark entrypoint:
  - `conda run -n morph-engine python scripts/run_experiment.py`

## Current Test Focus
- kernel smoke and semantic sanity:
  - `morph_engine/tests/test_vector_gs_kernel_v1.py`
- original runtime policy and alignment tests:
  - `morph_engine/tests/test_policy_study_v1.py`
  - `morph_engine/tests/test_runtime_grammar_alignment.py`

## Known Duplication Risk
There are currently two active representations of vector-GS generation logic:
- the original layered Bonobo runtime
- the standalone vector GS kernel

This is intentional for now, but it creates duplication risk in:
- structural semantics
- rule behavior
- artifact schemas
- viewer support

The expected long-term bridge is adapter-based rather than a direct collapse of one system into the other.

## Immediate Next Work
- reproducible kernel experiments
- benchmark/problem definitions for kernel evaluation
- metrics and artifact clarity
- policy comparison over the kernel if justified
- viewer support and stepwise inspection

Project Summary — Bonobo
1️⃣ Vision

Bonobo is a:

Grammar-driven structural generation engine

Physics-constrained discovery system

Designed to:

Explore diverse equilibrium forms (Juney-style)

Generate goal-oriented structures

Eventually integrate GNN + RL

Core ambition:

Structural language + physics semantics + learned policy over derivations.

🏗 Current Architecture (Stable)
Four-Layer Model
1. Canonical Representation

StructuralGraph

JSON schema v0.3

Nodes, edges, supports, loads

temp_force mechanism

2. Grammar

Rules:

connect_nodes

extend_node

split_edge

resolve_temp_force_v1

Deterministic propose/apply pattern

3. Evaluator (Physics Semantics)

Channels implemented:

geometry_planar_v1

global_equilibrium_v1

reaction_absorption_v1

structural_redundancy_v1

unbalanced_force_v1

maxwell_v1

Evaluator pipeline:

Deterministic

Context passing

Channel ordering stabilized

4. Learning (Planned)

GraphEncoder (not implemented yet)

PyG integration (future)

Policy head

RL loop

Diversity archive

🧪 Physics Status

✔ Load API implemented
✔ Temp force propagation works
✔ Reaction absorption works
✔ Equilibrium detection works
✔ Structure terminates when balanced

You validated:

Growth → propagate → absorb → terminate

19 tests passing, 1 skipped

Engine is stable.

🗂 Repository Governance (Now Industry-Grade)
Repo Renamed

panther → bonobo

GitHub Repo Created

vishnu-rajasekar/bonobo

Governance Files Added

AGENTS.md

SKILL.md

CONVENTIONS.md

ROADMAP.md

CHANGELOG.md

docs/

ARCHITECTURE.md

FILE_HIERARCHY.md

RESEARCH_LOG.md

Milestone Created

v0.5 – Experiment Harness

Issues Created

Logger_v1

Config system

Deterministic seed handling

🧩 Immediate Next Phase
Phase 2 — Experiment Harness

Goal:
Move from “engine” → “discovery system”

To Implement:

ExperimentRunner_v1

Logger_v1

Config loader

Deterministic seed handling

Output:
experiments/runs/<timestamp>/
    config.json
    final_graph.json
    trace.json
    metrics.json

This becomes:

Dataset

Foundation for diversity archive

Foundation for RL

🌿 Planned After Harness
DiversityArchive_v1

Descriptor vector

Novelty metric

Archive of equilibrated forms

Later:

MAP-Elites

Goal steering

GNN policy

🏷 Versioning Strategy

Tag stable checkpoints:

v0.4.0 → Stable physics engine

v0.5.0 → Experiment harness

v0.6.0 → Diversity archive

v0.7.0 → GNN integration

Tag ≠ branch.

Tag = immutable snapshot of a commit.

🔄 Where We Are Right Now

✔ Core engine stable
✔ Governance established
✔ Repo online
✔ Milestones created
🔜 Implement ExperimentRunner + Logger

📋 Clean Handover Brief for New Chat

You can paste this into a new chat:

Project: Bonobo

We are building a structural grammar engine for equilibrium-based form discovery.

Current state:

4-layer architecture:

StructuralGraph

Grammar rules

Evaluator channels

Learning (planned)

Force propagation and reaction absorption working.

19 tests passing.

Governance files created.

GitHub milestone: v0.5 – Experiment Harness.

Next task:
Implement ExperimentRunner_v1 and Logger_v1 in:
morph_engine/morph_engine/experiments/

Constraints:

Do not modify core engine.

Deterministic behavior.

Save experiment logs to experiments/runs/<timestamp>.

After harness, we will design DiversityArchive_v1.
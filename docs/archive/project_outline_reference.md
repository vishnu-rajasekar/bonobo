Historical reference only. Archived during documentation consolidation.

This file preserves broader exploratory architecture thinking from an earlier phase, including ideas that are no longer current repo guidance.

Below is a **clean, reusable reference architecture** you can drop into another chat and immediately start executing against. I’ll keep it concrete, opinionated, and aligned with your Airy-first / hybrid GS workflow.

---

# Reference Architecture

**Structural Morphology Engine + COMPAS-Aware Agent**

This architecture has **three layers**:

1. **Core Engine (physics + grammar)**
2. **Evaluation & Learning Layer (GS + RL)**
3. **Knowledge & Agent Layer (RAG, tools, execution)**

You already have (1) conceptually. The big win now is (3).

---

## 1. Core Engine (unchanged, but clarified)

This is what the agent *helps you build*, not what it replaces.

### Canonical representations

* **StructuralGraph (COMPAS Network / Mesh)**
* **Discrete Airy / stress-function state** (canonical equilibrium encoding)
* **Grammar actions** (topology + geometry)
* **Feasibility filters** (hard constraints)

> **Rule:**
> The agent never invents physics. It only helps you wire and reuse *known-safe* components.

---

## 2. Evaluation & Learning Layer (GS + DQN)

This is where your *new* insight matters.

### Graphic statics strategy (locked-in decision)

**Canonical state for learning**

* Discrete Airy / stress-function features
  (slopes, differences, ridge/valley structure, load-path proxies)

**Evaluation operators**

* Vector-based GS

  * Always available
  * Used during incremental growth
* Polyhedral GS

  * Only when grammar produces valid cell decompositions
  * Used for gridshell / fabrication-aware scoring

**Learning**

* DQN (not Q-table)
* Policy suggests:

  * grammar action
  * target entity (edge, face, node)
* Feasibility filters remain *hard gates*

This keeps:

* RL signal stable
* equilibrium guaranteed
* GS interchangeable

---

## 3. Knowledge & Agent Layer (this is the new architecture)

This is where your checklist fits. Think of this as a **COMPAS-aware design copilot**, not a generic LLM.

---

# Agent Architecture (drop-in reference)

## A. Knowledge sources (RAG-first, no fine-tuning initially)

### 1. Selective COMPAS documentation RAG

Index **only what the agent needs to reason structurally**.

**Include**

* COMPAS datastructures:

  * `Network`, `Mesh`, `VolMesh`
* Geometry basics:

  * vectors, frames, transformations
* Algorithms:

  * graph traversal
  * shortest paths
  * adjacency
* Relevant submodules:

  * `compas_ags`
  * `compas_3gs`
  * `compas_fd` (for sanity checks)

**Exclude**

* Visualization fluff
* Deprecated APIs
* Non-structural examples

> Goal: API correctness, not encyclopedic knowledge.

---

### 2. Canonical script index (10–20 max)

This is **critical**.

Index:

* Juney Lee–style vector GS scripts
* Your previous Q-learning GS experiment
* One clean AGS example
* One clean 3GS example
* One COMPAS Network grammar script
* One rigidity / Maxwell count script
* One load-path / force-length computation

Each script should have:

* filename
* COMPAS version
* short “what this proves” note

This becomes your **living lab notebook**.

---

### 3. Your own working code (highest priority)

Index:

* Anything that:

  * runs
  * you trust
  * encodes decisions you already made

The agent should **prefer your code over docs**.

---

### 4. Version metadata (non-negotiable)

Every indexed chunk must carry:

* COMPAS version
* Python version
* OS (important for Rhino later)

This prevents 80% of silent breakage.

---

## B. Tools the agent is allowed to use

### 1. Python execution tool (mandatory)

* Run small COMPAS snippets
* Validate assumptions
* Check object schemas

> This is how the agent “asks better internal questions”.

---

### 2. File system awareness

* Read / write project files
* Modify boilerplate
* Add tests

---

### 3. (Later) Rhino / MCP bridge

Not now, but architecturally reserved:

* Serialize `StructuralGraph`
* Transport Airy state
* Keep GS results decoupled from UI

---

## C. What the agent is **not** allowed to do

This is just as important.

* ❌ Invent GS theory
* ❌ Bypass feasibility filters
* ❌ Rewrite grammar logic “for elegance”
* ❌ Tune neural nets before RAG stabilizes

---

## D. Development workflow (agent + human)

### Phase 1 — Deterministic core

You + agent:

* Implement grammar actions
* Implement feasibility filters
* Implement GS evaluators
* No ML yet

Agent role:

* API correctness
* wiring help
* refactoring assistance

---

### Phase 2 — Assisted search (no learning)

* Beam search / annealing
* GS-based scoring
* Airy-derived features logged

Agent role:

* help instrument logging
* keep representations consistent

---

### Phase 3 — DQN integration

Only now:

* Replay buffer from Phase 2
* DQN policy replaces heuristic ranking
* Filters remain hard

Agent role:

* help design state tensors
* debug training loops
* compare learned vs heuristic actions

---

### Phase 4 — Optional fine-tuning

Only when:

* RAG answers are consistently correct
* You see repeated reasoning patterns

Fine-tune on:

* “Given this COMPAS graph + GS state, what actions are invalid?”
* “Given this failure, what feasibility rule was violated?”

---

# Concrete recommendation checklist (final form)

You can paste this verbatim into another chat:

---

### Concrete recommendation checklist

**If you want good performance quickly:**

* [ ] Set up **RAG on COMPAS docs (selective)**
* [ ] Index **10–20 canonical COMPAS + GS scripts**
* [ ] Index **your own working code first**
* [ ] Add **COMPAS + Python version metadata**
* [ ] Enable **Python execution as a tool**
* [ ] Delay **fine-tuning until RAG stabilizes**

**Architectural decisions (locked):**

* [ ] Airy / stress-function = canonical learning state
* [ ] Vector GS = always-available evaluator
* [ ] Polyhedral GS = conditional, cell-based mode
* [ ] Feasibility filters = hard constraints
* [ ] DQN suggests actions, never applies them directly

**If you do this, the agent will:**

* Use correct COMPAS APIs
* Ask better internal questions
* Make fewer structural mistakes
* Improve rapidly as you add examples
* Stay aligned with Maxwell + GS theory

---

## What I can help you do next (in order of leverage)

1. **Propose a minimal COMPAS knowledge base outline** (exact folders + docs to index)
2. **Identify the 10 most important COMPAS scripts** for your project
3. **Design a COMPAS ↔ Rhino ↔ MCP data model**
4. **Draft DQN state/action/reward tensors (Airy-based)**
5. **Suggest fine-tuning prompts once RAG is solid**

If you want, say **“Start with (1)”** or **“Jump to (4)”**, and we’ll go straight there without rehashing theory.

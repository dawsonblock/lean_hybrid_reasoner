# Lean-Dojo Ecosystem Integration

This repository integrates Lean-Dojo projects as staged optional adapters. It does not vendor or tightly couple the whole ecosystem into core proof-search runtime paths.

## Classification

Core dependency and main backend target:

- LeanDojo-v2

Editor/in-Lean integration:

- LeanCopilot

Long-term lifelong learning:

- LeanAgent

Optional future retrieval/model references:

- ReProver-style premise retrieval and tactic generation ideas (not implemented in this phase)

Research-only:

- TorchLean
- LeanProgress (if the project later expands into related research workflows)

Do not integrate as primary runtime targets:

- legacy lean-dojo/LeanDojo as primary backend
- BRIDGE while empty

## Why LeanDojo-v2 is first

The existing Lean CLI backend is file/subprocess oriented and intentionally lightweight. LeanDojo-v2 is the correct backend upgrade path because it supports repository tracing, structured theorem/proof-state extraction, theorem databases, retrieval-augmented proving, Pantograph-style interaction, training paths, and external inference API support.

## Integration order

1. LeanDojo-v2 backend adapter.
2. ReProver-style premise retriever later.
3. DSPy training activation using trace datasets.
4. LeanCopilot external API bridge.
5. LeanAgent-style curriculum/repository database.
6. TorchLean only if this project moves into ML/tensor verification.

## Critical warning

The Lean-Dojo ecosystem must be integrated through optional adapters. The core proof-search engine must not be rewritten around external project internals.

Keep `ProofSearchEngine` backend-agnostic and maintain stable support for:

- mock
- lean_cli
- leandojo_v2

## Dependency policy

The `leandojo`, `copilot`, `leanagent`, and `ecosystem` extras are intentionally optional and may remain empty when package names are uncertain.

Install ecosystem repos separately from GitHub in environment-specific workflows rather than forcing hard runtime dependencies in this repository.

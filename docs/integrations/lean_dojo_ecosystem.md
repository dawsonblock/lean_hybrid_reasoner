# Lean-Dojo Ecosystem Integration Plan

This document defines how Lean Hybrid Reasoner adopts Lean-Dojo ecosystem projects in stages, without turning them into one giant dependency.

## Goal

Keep the current proof-search shell stable while adding missing capabilities through optional adapters:

- stateful Lean interaction
- repository tracing
- stronger premise retrieval
- in-Lean copilot workflows
- long-term cross-repository training infrastructure

## Classification

| Repo | Status | Reason |
| --- | --- | --- |
| LeanDojo-v2 | Core dependency, first | End-to-end Lean 4 AI theorem-proving framework with repository tracing, theorem/proof-state data, retrieval-augmented proving, and training paths. |
| lean-dojo/LeanDojo (legacy) | Do not use for new integration | Deprecated for new work; keep as historical reference only. |
| LeanCopilot | Later, optional | In-Lean tactic suggestion/proof search and model integration for editor-facing workflows. |
| ReProver | Optional retrieval/model reference | Strong premise retrieval and tactic generation ideas; useful to upgrade retrieval quality. |
| LeanAgent | Later, research layer | Lifelong learning over many repositories with curriculum and dynamic database management. |
| TorchLean | Research-only, out of core scope | Useful for formal ML/tensor verification, not required for theorem proving core. |
| BRIDGE | Skip for now | Repository currently empty; no actionable integration target. |
| lean-dojo org page | Bookmark only | Discovery source, not a runtime dependency. |

## Why LeanDojo-v2 first

The existing Lean CLI backend validates architecture, but remains subprocess/text-parsing oriented.

LeanDojo-v2 is the correct next backend because it enables:

- repository tracing
- structured theorem/proof-state extraction
- theorem database workflows
- retrieval-augmented proving
- Pantograph-based Lean interaction
- SFT/GRPO/retriever training paths
- external inference API integration

## Integration contract

The proof search engine remains backend-agnostic by preserving the existing protocol contract.

```python
class LeanBackend(Protocol):
    def list_theorems(self) -> list[str]: ...
    def load_theorem(self, theorem_name: str) -> LeanProofState: ...
    def execute_tactic(self, state: LeanProofState, tactic: str) -> LeanExecutionResult: ...
```

LeanDojo-v2 integration target:

- `src/lean_hybrid_reasoner/lean_backend/leandojo_v2_client.py`

## Correct integration order

1. LeanDojo-v2 backend adapter.
2. ReProver-style retriever upgrade (optional retrieval mode).
3. DSPy training activation on trace datasets.
4. LeanCopilot external API bridge for in-Lean workflows.
5. LeanAgent-style repository DB + curriculum layer.
6. TorchLean only if formal ML verification becomes a product goal.
7. Keep BRIDGE out until it has implementable code.

## What this phase implements

This phase intentionally includes only:

- this roadmap document
- `leandojo_v2_client.py` backend adapter seam

It intentionally does not include:

- runtime backend selection wiring (`LHR_BACKEND=leandojo_v2`)
- new retrieval mode implementation (`reprover`)
- LeanCopilot runtime bridge
- LeanAgent training/database pipeline

## Design rule

Do not import the whole Lean-Dojo ecosystem into core runtime paths.

Use optional adapters around each external project so existing `mock` and `lean_cli` flows remain stable.

# LeanCopilot Bridge (Planned)

LeanCopilot integration is planned as a future editor-facing bridge, not a core runtime dependency in this phase.

## Target workflow

Lean editor
  -> LeanCopilot tactic request
  -> external API endpoint from lean_hybrid_reasoner
  -> ProofSearchEngine / proposer
  -> candidate tactic
  -> Lean verifies tactic

## Scope in this phase

- Document architecture and boundaries.
- Keep runtime optional and non-breaking.
- Do not implement a live server yet.

## Future module target

- `src/lean_hybrid_reasoner/copilot/external_api_server.py` (future)
- adapter wiring to local or hosted model providers

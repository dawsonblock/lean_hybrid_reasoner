# Upgrade Notes v0.7

This release adds staged Lean-Dojo ecosystem integration seams while keeping existing proof-search architecture stable and test-safe.

## Added

- LeanDojo-v2 adapter seam:
  - `src/lean_hybrid_reasoner/lean_backend/leandojo_v2_client.py`
- Ecosystem integration documentation:
  - `docs/integrations/lean_dojo_ecosystem.md`
  - `docs/integrations/leancopilot_bridge.md`
  - `docs/integrations/leanagent_lifelong_learning.md`
- Ecosystem status command:
  - `hybrid-proof ecosystem-status`
- Doctor ecosystem diagnostics:
  - backend availability matrix includes LeanDojo-v2 adapter status
  - ecosystem section for LeanDojo-v2, LeanCopilot, LeanAgent
- Future placeholder packages:
  - `src/lean_hybrid_reasoner/copilot/`
  - `src/lean_hybrid_reasoner/lifelong/`
- Optional dependency groups in `pyproject.toml`:
  - `leandojo`, `copilot`, `leanagent`, `ecosystem`

## Behavior and compatibility

- No hard dependency on LeanDojo-v2, LeanCopilot, or LeanAgent is introduced.
- `mock` backend remains default and test-safe.
- Existing trace/replay/dataset commands remain backward-compatible.
- No external repository is cloned automatically.
- Tests and local status commands run without network access.

## Backend selection

Supported `LHR_BACKEND` values now include:

- `mock`
- `lean_cli`
- `leandojo`
- `leandojo_v2`

LeanDojo-v2 remains a defensive adapter seam when dependency/runtime wiring is not fully configured.

## Commands

```bash
hybrid-proof doctor
hybrid-proof ecosystem-status
hybrid-proof list-theorems
```

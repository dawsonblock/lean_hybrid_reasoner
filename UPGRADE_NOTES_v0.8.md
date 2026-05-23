# Upgrade Notes v0.8

## Summary

v0.8 activates DSPy training workflows and hardens tactic output handling while keeping DSPy optional.

## Highlights

- Added tactic sanitizer and validator modules.
- Sanitizer integrated into heuristic and DSPy tactic candidate paths.
- Search engine now rejects invalid tactic outputs before backend execution.
- Added DSPy dataset loader independent of DSPy install for raw loading.
- Added DSPy metric helpers for tactic matching and verifier-backed scoring.
- Added compiled artifact manifest schema and validation.
- Added train-dspy-proposer and train-dspy-repairer CLI commands with dry-run mode.
- Added compare-proposers command for heuristic vs heuristic baseline and optional DSPy comparison.
- Extended pack-dataset with target/quality/sanitizer options.
- Added shared user-facing CLI error handling for optional dependency failures.

## Backward Compatibility

- Mock backend remains default.
- LeanDojo-v2 remains staged and optional.
- Existing run/eval/replay/trace export flows remain available.
- DSPy remains optional under extras.

## Optional Dependency

```bash
pip install -e ".[llm]"
```

Dry-run training commands work without DSPy.

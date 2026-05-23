# Tactic Sanitization

The tactic sanitization layer prevents malformed model outputs from reaching backend tactic execution.

## What is sanitized

- Markdown code fences.
- Surrounding quotes.
- Leading bullets and list numbering.
- Prefixes like `Tactic:` and `Use:`.

## What is rejected

- Empty output.
- Natural language explanations.
- Outputs longer than configured max length.
- `sorry` and `admit` by default.
- Multiple unrelated tactic suggestions when multiline is disabled.

## Trace metadata

Rejected and executed tactic events include:

- `raw_tactic`
- `tactic`
- `tactic_sanitized`
- `tactic_sanitizer_warnings`

This metadata allows downstream audits and dataset filtering to reason about model output quality.

# LeanAgent Lifelong Learning Layer (Planned)

LeanAgent maps to long-term repository-scale theorem proving and continuous improvement workflows.

## Target lifecycle

many Lean repositories
  -> repository tracing
  -> theorem/proof-state database
  -> difficulty/curriculum ranking
  -> retriever/proposer training
  -> best-first proof search
  -> solved trace storage
  -> repeat

## Scope in this phase

- Document intended architecture.
- Keep implementation out of core runtime for now.
- Preserve current stable proof-search shell and traces.

## Future module target

- repository ingestion and trace orchestration
- curriculum scheduler
- retriever/proposer training loop coordinator

# COMPOSE

COMPOSE is a Reflex architecture assembly workspace with seven routes: dashboard, primitives, rules, composer, conflicts, goals and saved designs. Existing CRUD remains available. The canvas uses enterprise React Flow with per-primitive typed handles. Saved records are database-backed; draft changes and undo/redo history are session-local.

## Local run

Use Python 3.13 and install requirements with pip. Run `reflex run` from the project root, then open the frontend URL printed by Reflex. A working PostgreSQL connection must be supplied by your environment; never put credentials in source control. The managed environment supplies storage and applies model migrations. This change does not alter the database schema or initialize tables. Consult Reflex documentation for setting up storage in an independent local environment.

## Walkthrough

1. Open the dashboard Protected stack scenario, or load a design from Saved.
2. Add blocks from the library; drag them into place. Connect an output handle to a matching input handle. Invalid edges remain visible and produce actionable findings.
3. Select a node/edge and use Delete selected. Undo/Redo restores graph snapshots, including positions and edges.
4. Open Conflicts to inspect Conflict DNA and verified single-edit repairs. Apply a repair, return to Composer, and save. Choose Save as new to preserve a reference design.
5. In Goals choose Protected API, Observable async, or Impossible dual database. Edit the JSON selectors, preferences and budgets. Open any evaluated candidate in Composer and save it.
6. In Saved load, rename, explicitly confirm deletion, or export JSON. Exported snapshots are historical; live loading re-evaluates current rules.

## Tests

Run `python -m pytest tests`. Tests cover all rule families, emergent three-way conflicts, typed edges, required ports, verified repairs, bounded search outcomes, snapshot history and API requests with an isolated repository stub. Tests do not require a database. These tests are provided but were not executed during this implementation. See `docs/testing.md` for manual end-to-end and concurrency checks.

## Additional documentation

- `docs/rule-parameters.md`: stored parameter semantics.
- `docs/api.md`: public read/evaluation/search API contract.
- `docs/architecture.md`: evaluation and search concepts.
- `docs/local-and-hosting.md`: local operation and hosting limitations.
- `docs/environment-example.txt`: safe environment setup checklist, without secrets.

Hosting is not provisioned here. No Vercel or Render deployment is claimed. The current API is intended for a trusted workspace; authentication/authorization must be added before public exposure.

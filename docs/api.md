# COMPOSE REST API

The Reflex backend exposes FastAPI routes and generated OpenAPI documentation at `/api/docs` (`/api/openapi.json`). These endpoints do not override Reflex runtime routes. All reads return current database data; expensive work runs outside the event loop.

- GET `/api/primitives`: primitive IDs, keys, descriptions, costs, properties and typed ports.
- GET `/api/rules`: rule IDs, type, severity, enabled flag and JSON parameters.
- GET `/api/compositions`: saved graph records and historical validation snapshots.
- GET `/api/compositions/{key}`: one saved graph; 404 with not_found if absent.
- POST `/api/validate`: graph body with nodes and edges; returns status, valid, findings, effects, cost, grouped DNA and verified repair proposals.
- POST `/api/solve`: selectors, optional preferences, max_cost, max_blocks, time_budget and node_budget; returns explicit outcome, verified ranked solutions, visited count, elapsed time, completeness and domain description.

List routes accept `limit` (1–500, default 100) and `offset` (nonnegative). Results contain items and total.

A graph node requires id and primitive_key, and optionally position with finite x/y. An edge requires id, source, target, source_port and target_port. Graph arrays are limited to 100 nodes and 300 edges. Unknown fields are rejected. A valid body with an incompatible edge returns HTTP 200 with an invalid evaluation; malformed request structure returns HTTP 422.

Selectors contain keys, category and/or properties. Goal costs are nonnegative finite numbers; max_blocks is an integer 0–30, time_budget 0–10 seconds, node_budget an integer 0–200000. Defaults are documented in the Goals UI. Returned budget-exhausted candidates are verified but ranking is provisional. Proven-impossible is relative to the finite domain, not all conceivable architectures.

Errors use an error object containing code and message; malformed bodies also include safe path/message details. Codes: invalid_body (422), invalid_semantics (422), not_found (404), workspace_unavailable (503). Responses never include database connection details or stack traces.

This is a trusted-workspace API without built-in authentication. Do not publicly expose it without an authorization layer and request limits. Writes remain in the existing Reflex UI flows; no unauthenticated REST write endpoints are added.

# COMPOSE rule parameters — version 1

The dashboard, Rule Doctor and demo composition snapshots share `app/services/rule_schema.py`. Parameters are stored in the existing rule JSON column. Unknown parameter fields, unknown primitive keys, non-finite numbers and invalid selectors are rejected on save. Disabled rules are ignored. Rules operate on composition node occurrences, not unique primitive keys.

## Selectors

A selector is a nonempty object with any of `keys` (nonempty array of stable primitive key strings), `category` (nonempty string), and `properties` (nonempty object of exact-match property values). Fields combine with AND. Keys within the array combine with OR. Matching is case-sensitive. Properties use exact equality, not expression evaluation. Copy stable keys from primitive cards. Custom categories are allowed. Category/property selectors can be defined before matching primitives exist; Rule Doctor flags empty requirement targets.

## Rule types

- **pairwise**: `a`, `b` selectors and `relation` = `require` or `exclude`. Require means presence of any A needs at least one B. Exclude prohibits simultaneous A and B. Require is directional; exclude is symmetric.
- **conditional**: `when`, `require` selectors. Presence of any `when` node requires at least one matching `require` node.
- **exclusive**: `members` (at least two selectors), `max_count` (nonnegative integer). Count node occurrences matching any member, without counting one node twice when selectors overlap. Constrain that count to max_count.
- **quantitative**: `metric` = `cost`, `node_count`, or `property`; optional `scope` selector; `min` and/or `max` inclusive nonnegative numeric bounds. For metric=property, `property` is required and names the numeric property to sum. This field is forbidden for other metrics. Cost sums monthly estimates; node_count counts occurrences; property sums matching nodes' property values, missing values default to zero. Nonnumeric property values produce an evaluation error. Empty scope contributes zero. Bounds cannot be reversed. Omitted minimum is zero; omitted maximum is unbounded.
- **emergent**: `all` (at least two selectors), `effect` (nonempty string). When every selector has a matching node, report the capability. Optional outcome is capability (default for existing records) or conflict. Capability reports an effect; conflict reports a finding at the configured severity. Every selector must match for either outcome.

Severity is `error`, `warning`, or `info`. Only error findings invalidate a node-constraint evaluation. Explanation is required; repair_hint is an optional actionable suggestion, not an automatically verified repair.

## Primitive JSON

Properties and metadata must be JSON objects. Ports must be an array of objects with unique nonempty `name`, `direction` = `input` or `output`, and nonempty `type` (protocol such as http, sql, event). Optional `required` and `multiple` are booleans. Other port fields are rejected. Types must match exactly to connect. The live graph evaluator enforces edge direction, required-port completeness and multiplicity. Ports default to single connection unless multiple=true. Required unconnected ports produce partial status; invalid edges produce invalid status. Metadata does not participate in selectors.

## Composition interchange foundation

Demo node objects contain `id`, `primitive_key` and `position` with x/y coordinates. Edge objects contain `id`, `source`, `source_port`, `target`, `target_port`. Demo edges are added only when adjacent port types match. Validation snapshots contain `schema_version`, `valid`, `findings`, `effects`, and `evaluation_scope`. Results are calculated from primitive data and enabled rules, never preset labels. Seed snapshots are historical node evaluations. Loaded graphs use the shared live node/edge evaluator; saves write version 2 graph validation snapshots. Subsequent rule edits do not silently claim that saved snapshots are revalidated.

## Rule Doctor scope

Enabled rules are schema-checked against current library keys. Require/conditional versus exclude conflicts are detected when all currently matching trigger and target candidates are prohibited by an exclusion (including reversed exclusion direction). Equal quantitative metric/property/scope signatures are checked pairwise for disjoint intervals. Disabled rules are ignored; severity is shown on rule cards and all enabled-rule inconsistencies are reported as potential issues. This is intentionally a targeted diagnostic, not a SAT solver. The Goals lab now provides bounded finite-domain search and distinguishes exhaustive impossibility from budget exhaustion. Rule Doctor remains a targeted diagnostic.

## Demo and persistence

Initialization safely inserts missing reserved demo keys under a transaction-scoped PostgreSQL advisory lock: 24 curated System Architecture components, 19 constraints spanning all types, five composition examples and activity in one transaction. Reset replaces records whose stable keys have the reserved `demo:` prefix, preserving custom records and references to those stable keys. Reset also removes demo-associated history and records a fresh reset event. Deletion of a primitive is blocked when a saved composition or any rule explicitly references it. All create/update/delete/toggle operations record activity transactionally. Refresh and route load fetch current persisted records; local state is only a rendering cache and editor draft.

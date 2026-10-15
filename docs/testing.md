# Testing checklist

Automated backend checks: run `python -m pytest tests`. The API tests replace repository reads with isolated fixture data. No network/database credentials are required. Pure evaluation, search and snapshot helper tests are deterministic apart from bounded wall-clock search time. An actual browser runner and isolated managed-database fixture are not available in this editing environment, so frontend and live persistence/concurrency tests are manual rather than claimed as executed automation.

## End-to-end browser checks

- Open all seven desktop and mobile nav routes.
- Load Protected stack from Dashboard; add a primitive, drag it, connect matching handles and confirm live validity. Connect incompatible protocols and inspect the edge reason.
- Select/delete a node with edges; Undo restores both, Redo removes both. Undo then add a node: Redo must not restore the abandoned branch.
- Load Three-way conflict. Confirm emergent DNA includes three nodes. Apply a verified removal, inspect reduced errors and save as new.
- Refresh Saved and load the new graph; check positions, edges and validation. Rename, export JSON, confirm deletion, refresh and verify absence.
- Exercise existing primitive/rule create/edit/delete/toggle and Reset. Custom records must survive Reset.
- Run both satisfiable Goals presets and open verified candidates. Run dual-database goal: proven-impossible. Set node_budget to zero: budget-exhausted without an invented candidate.
- Edit a rule, refresh Composer and verify current rules override historical saved validation.

## Database concurrency checks (isolated workspace only)

Use a disposable database with the managed schema already applied. Trigger simultaneous startup/page loads in independent sessions; expect a single row per stable demo key, with 24 demo primitives, 19 demo rules and 5 demo compositions. No duplicate-key exception should occur. Repeat after editing a demo record: normal initialization must preserve the edit. Inject a database connection failure, verify a surfaced retry message, restore connectivity and refresh; a fresh session must succeed rather than reuse an aborted transaction.

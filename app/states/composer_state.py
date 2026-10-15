import reflex as rx

import asyncio
import json
import logging
from copy import deepcopy
from typing import Any
from uuid import uuid4
from reflex_enterprise.components.flow.types import Node, Edge

from app.services.engine import (
    canonical,
    evaluate_graph,
    verified_repairs,
    apply_repair,
    push_history,
)
from app.services.repository import (
    read_workspace,
    save_composition,
    change_saved,
)
from app.services.solver import solve, PRESETS


class ComposerState(rx.State):
    nodes: list[Node] = []
    edges: list[Edge] = []
    library: list[dict[str, str]] = []
    saved: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []
    effects: list[str] = []
    dna: list[dict[str, str]] = []
    repairs: list[dict[str, str]] = []
    solutions: list[dict[str, str]] = []
    status: str = "partial"
    cost: float = 0.0
    title: str = "Untitled composition"
    composition_key: str = ""
    undo_stack: list[str] = []
    redo_stack: list[str] = []
    busy: bool = False
    error: str = ""
    notice: str = ""
    search_result: str = "Choose a preset or define a goal."
    goal_json: str = json.dumps(PRESETS["Protected API"], indent=2)
    rename_key: str = ""
    _primitives: list[dict] = []
    _rules: list[dict] = []
    _saved_records: list[dict] = []
    _repair_records: list[dict] = []
    _solution_records: list[dict] = []
    revision: int = 0

    def _graph(self) -> dict:
        return canonical(self.nodes, self.edges)

    def _flow(self, graph: dict):
        library = {p["key"]: p for p in self._primitives}
        self.nodes = [
            {
                **n,
                "type": "primitive",
                "data": {
                    "label": library.get(n["primitive_key"], {}).get(
                        "name", n["primitive_key"]
                    ),
                    "primitive_key": n["primitive_key"],
                    "ports": library.get(n["primitive_key"], {}).get(
                        "ports", []
                    ),
                },
            }
            for n in graph["nodes"]
        ]
        self.edges = [
            {
                **e,
                "sourceHandle": e["source_port"],
                "targetHandle": e["target_port"],
                "type": "smoothstep",
            }
            for e in graph["edges"]
        ]

    def _remember(self):
        self.undo_stack, self.redo_stack = push_history(
            self.undo_stack, json.dumps(self._graph()), self.redo_stack
        )
        self.revision += 1
        self.notice = "Unsaved changes"

    def _apply_evaluation(self, result: dict, repairs: list[dict]):
        self.status, self.cost = result["status"], result["cost"]
        self.findings = [
            {
                "rule_id": f["rule_id"],
                "reason": f["reason"],
                "severity": f["severity"],
                "nodes": ", ".join(f["node_ids"]),
                "hint": f["repair_hint"],
                "root_cause": f["root_cause"],
            }
            for f in result["findings"]
        ]
        self.effects = result["effects"]
        self.dna = [
            {
                "cause": d["root_cause"],
                "rules": ", ".join(d["rule_ids"]),
                "nodes": ", ".join(d["node_ids"]),
                "count": str(d["count"]),
            }
            for d in result["dna"]
        ]
        self._repair_records = repairs
        self.repairs = [
            {
                "index": str(i),
                "label": p["label"],
                "detail": f"{p['edit_count']} edit · resolves {p['resolved']} error(s) · {p['remaining']} remaining · {p['status_after']}",
            }
            for i, p in enumerate(repairs)
        ]

    @rx.event(background=True)
    async def load(self):
        async with self:
            if self.busy:
                return
            self.busy = True
            self.error = ""
        try:
            data = await asyncio.to_thread(read_workspace)
            async with self:
                self._primitives, self._rules, self._saved_records = (
                    data["primitives"],
                    data["rules"],
                    data["saved"],
                )
                self.library = [
                    {
                        "key": p["key"],
                        "name": p["name"],
                        "category": p["category"],
                        "cost": f"{p['cost']:.2f}",
                    }
                    for p in data["primitives"]
                ]
                self.saved = [
                    {
                        "key": c["key"],
                        "title": c["title"],
                        "updated": c["updated_at"],
                        "blocks": str(len(c["nodes"])),
                    }
                    for c in data["saved"]
                ]
                requested = self.router.url.query_parameters.get(
                    "composition", ""
                )
                record = next(
                    (c for c in data["saved"] if c["key"] == requested), None
                )
                if record and requested != self.composition_key:
                    self._open_record(record)
                else:
                    self._flow(self._graph())
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Could not load workspace data. Try Refresh."
        finally:
            async with self:
                self.busy = False
        yield ComposerState.validate

    def _open_record(self, record: dict):
        self._flow({"nodes": record["nodes"], "edges": record["edges"]})
        self.title, self.composition_key = record["title"], record["key"]
        self.undo_stack, self.redo_stack = [], []
        self.revision += 1
        self.notice = "Loaded composition"

    @rx.event
    def open_saved(self, key: str):
        record = next((c for c in self._saved_records if c["key"] == key), None)
        if record:
            self._open_record(record)
            yield rx.redirect("/composer")
            yield ComposerState.validate
        else:
            self.error = "Composition no longer exists. Refresh the list."

    @rx.event
    def add_primitive(self, key: str):
        if not any(p["key"] == key for p in self._primitives):
            return
        self._remember()
        graph = self._graph()
        graph["nodes"].append(
            {
                "id": uuid4().hex[:10],
                "primitive_key": key,
                "position": {
                    "x": (len(self.nodes) % 4) * 260,
                    "y": (len(self.nodes) // 4) * 180,
                },
            }
        )
        self._flow(graph)
        yield ComposerState.validate

    @rx.event
    def set_nodes(self, nodes: list[Node]):
        old = self._graph()
        new = canonical(nodes, self.edges)
        new["edges"] = [
            e
            for e in new["edges"]
            if e["source"] in {n["id"] for n in nodes}
            and e["target"] in {n["id"] for n in nodes}
        ]
        if old != new:
            self._remember()
        self.nodes = nodes
        self.edges = [
            {
                **e,
                "sourceHandle": e["source_port"],
                "targetHandle": e["target_port"],
            }
            for e in new["edges"]
        ]
        yield ComposerState.validate

    @rx.event
    def set_edges(self, edges: list[Edge]):
        if canonical(self.nodes, edges) != self._graph():
            self._remember()
        self.edges = edges
        yield ComposerState.validate

    @rx.event
    def delete_selected(self):
        self._remember()
        selected = {n["id"] for n in self.nodes if n.get("selected")}
        self.nodes = [n for n in self.nodes if n["id"] not in selected]
        self.edges = [
            e
            for e in self.edges
            if not e.get("selected")
            and e["source"] not in selected
            and e["target"] not in selected
        ]
        yield ComposerState.validate

    @rx.event
    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(json.dumps(self._graph()))
            self._flow(json.loads(self.undo_stack.pop()))
            self.revision += 1
            yield ComposerState.validate

    @rx.event
    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(json.dumps(self._graph()))
            self._flow(json.loads(self.redo_stack.pop()))
            self.revision += 1
            yield ComposerState.validate

    @rx.event
    def new_composition(self):
        self._remember()
        self._flow({"nodes": [], "edges": []})
        self.title, self.composition_key = "Untitled composition", ""
        yield ComposerState.validate

    @rx.event(background=True)
    async def validate(self):
        async with self:
            graph, primitives, rules, revision = (
                self._graph(),
                deepcopy(self._primitives),
                deepcopy(self._rules),
                self.revision,
            )
        result = await asyncio.to_thread(
            evaluate_graph, primitives, rules, **graph
        )
        proposals = await asyncio.to_thread(
            verified_repairs, primitives, rules, graph
        )
        async with self:
            if revision == self.revision:
                self._apply_evaluation(result, proposals)

    @rx.event
    def repair(self, index: str):
        i = int(index)
        if i < 0 or i >= len(self._repair_records):
            return
        proposal = self._repair_records[i]
        before = evaluate_graph(self._primitives, self._rules, **self._graph())
        graph = apply_repair(self._graph(), proposal)
        from app.services.engine import error_signature

        after = evaluate_graph(self._primitives, self._rules, **graph)
        if not error_signature(after) < error_signature(before):
            self.error = "This repair is stale. Revalidate before applying."
            yield ComposerState.validate
            return
        self._remember()
        self._flow(graph)
        yield ComposerState.validate

    @rx.event
    def submit_save(self, data: dict[str, Any]):
        self.title = str(data.get("title", "")).strip()
        if data.get("save_as"):
            self.composition_key = ""
        yield ComposerState.save

    @rx.event(background=True)
    async def save(self):
        async with self:
            if self.busy:
                return
            self.busy = True
            key, title, graph, revision = (
                self.composition_key,
                self.title,
                self._graph(),
                self.revision,
            )
        try:
            key = await asyncio.to_thread(save_composition, key, title, graph)
            async with self:
                if revision == self.revision:
                    self.composition_key = key
                    self.notice = "Composition saved to the database."
                else:
                    self.notice = "Snapshot saved; newer edits remain unsaved."
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Save failed. Your graph is preserved."
                )
        finally:
            async with self:
                self.busy = False
        yield ComposerState.load

    @rx.event
    def choose_preset(self, name: str):
        self.goal_json = json.dumps(PRESETS[name], indent=2)

    @rx.event
    def submit_goal(self, data: dict[str, Any]):
        self.goal_json = str(data.get("goal", "{}"))
        yield ComposerState.search

    @rx.event(background=True)
    async def search(self):
        async with self:
            if self.busy:
                return
            self.busy = True
            text, primitives, rules = (
                self.goal_json,
                deepcopy(self._primitives),
                deepcopy(self._rules),
            )
            self.search_result = (
                "Searching with propagation and bounded backtracking…"
            )
            self.solutions = []
            self._solution_records = []
        try:
            goal = json.loads(text)
            if not isinstance(goal, dict):
                raise ValueError("Goal must be a JSON object.")
            result = await asyncio.to_thread(solve, primitives, rules, goal)
            async with self:
                self.search_result = f"{result['status']} · {result['visited']} search nodes · {result['elapsed_ms']:.1f} ms. {result['reason']}"
                self._solution_records = result["solutions"]
                self.solutions = [
                    {
                        "index": str(i),
                        "label": f"Candidate {i + 1} · {s['blocks']} blocks · ${s['cost']:.2f}",
                        "detail": f"{s['preferred']} preferences · {s['warnings']} warnings · verified valid",
                    }
                    for i, s in enumerate(result["solutions"])
                ]
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Search failed; no solution has been claimed."
                )
                self.search_result = "Invalid goal or search failure."
        finally:
            async with self:
                self.busy = False

    @rx.event
    def use_solution(self, index: str):
        s = self._solution_records[int(index)]
        self._remember()
        self._flow({"nodes": s["nodes"], "edges": s["edges"]})
        self.title, self.composition_key = "Goal solution", ""
        yield rx.redirect("/composer")
        yield ComposerState.validate

    @rx.event
    def ask_rename(self, key: str):
        self.rename_key = key

    @rx.event
    def submit_rename(self, data: dict[str, Any]):
        yield ComposerState.mutate_saved(
            self.rename_key, str(data.get("title", "")), False
        )

    @rx.event(background=True)
    async def mutate_saved(self, key: str, title: str, delete: bool):
        async with self:
            if self.busy:
                return
            self.busy = True
        try:
            await asyncio.to_thread(change_saved, key, title, delete)
            async with self:
                self.rename_key = ""
                self.notice = (
                    "Composition deleted." if delete else "Composition renamed."
                )
                self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Could not update composition."
                )
        finally:
            async with self:
                self.busy = False
        yield ComposerState.load

    @rx.event
    def export_saved(self, key: str):
        record = next((c for c in self._saved_records if c["key"] == key), None)
        if record:
            return rx.download(
                data=json.dumps(record, indent=2), filename="composition.json"
            )

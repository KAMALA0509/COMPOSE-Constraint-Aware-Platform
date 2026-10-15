import reflex as rx

from copy import deepcopy
from collections import Counter, defaultdict
from uuid import uuid4

from app.services.rule_schema import (
    evaluate,
    matches,
    validate_parameters,
    validate_ports,
)


def canonical(nodes: list[dict], edges: list[dict]) -> dict:
    return {
        "nodes": [
            {
                "id": n["id"],
                "primitive_key": n.get(
                    "primitive_key", n.get("data", {}).get("primitive_key", "")
                ),
                "position": n.get("position", {"x": 0, "y": 0}),
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e.get("id", uuid4().hex),
                "source": e["source"],
                "target": e["target"],
                "source_port": e.get("source_port", e.get("sourceHandle", "")),
                "target_port": e.get("target_port", e.get("targetHandle", "")),
            }
            for e in edges
        ],
    }


def evaluate_graph(
    primitives: list[dict],
    rules: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    graph = canonical(nodes, edges)
    nodes, edges = graph["nodes"], graph["edges"]
    library = {p["key"]: p for p in primitives}
    resolved = []
    findings = []
    effects = []

    def finding(
        key,
        reason,
        affected,
        category="constraint",
        severity="error",
        hint="",
        edge_ids=None,
        selector=None,
        rule_id="",
    ):
        findings.append(
            {
                "rule_key": key,
                "rule_id": str(rule_id or key),
                "severity": severity,
                "reason": reason,
                "explanation": reason,
                "node_ids": sorted(set(affected)),
                "edge_ids": edge_ids or [],
                "root_cause": category,
                "repair_hint": hint,
                "selector": selector or {},
            }
        )

    ids = [n["id"] for n in nodes]
    for duplicate, count in Counter(ids).items():
        if count > 1:
            finding(
                "graph:node-id",
                "Node IDs must be unique.",
                [duplicate],
                "graph",
            )
    for n in nodes:
        p = library.get(n["primitive_key"])
        if p is None:
            finding(
                "graph:unknown-primitive",
                f"Unknown primitive {n['primitive_key']}.",
                [n["id"]],
                "graph",
                hint="Remove this node or restore its primitive.",
            )
        else:
            try:
                validate_ports(p.get("ports", []))
                resolved.append({**p, "node_id": n["id"]})
            except ValueError as e:
                finding(
                    "graph:ports-schema",
                    str(e),
                    [n["id"]],
                    "schema",
                    hint="Correct the primitive ports in the library.",
                )
    by_id = {p["node_id"]: p for p in resolved}
    used = Counter()
    seen_edges = set()
    for e in edges:
        a, b = by_id.get(e["source"]), by_id.get(e["target"])
        affected = [e["source"], e["target"]]
        reason = ""
        if e["id"] in seen_edges:
            reason = "Edge IDs must be unique."
        seen_edges.add(e["id"])
        if a is None or b is None:
            reason = "Edge endpoint does not exist."
        else:
            out = next(
                (
                    p
                    for p in a.get("ports", [])
                    if p["name"] == e["source_port"]
                ),
                None,
            )
            inp = next(
                (
                    p
                    for p in b.get("ports", [])
                    if p["name"] == e["target_port"]
                ),
                None,
            )
            if out is None or inp is None:
                reason = "Edge references an unknown port."
            elif out["direction"] != "output" or inp["direction"] != "input":
                reason = "Connections must run from an output to an input."
            elif out["type"] != inp["type"]:
                reason = (
                    f"Incompatible port types: {out['type']} → {inp['type']}."
                )
            else:
                for node_id, port in ((e["source"], out), (e["target"], inp)):
                    used[(node_id, port["name"])] += 1
                    if used[(node_id, port["name"])] > 1 and not port.get(
                        "multiple", False
                    ):
                        reason = f"Port {node_id}/{port['name']} permits only one connection."
        if reason:
            finding(
                "graph:edge",
                reason,
                affected,
                "edge",
                hint="Remove or reconnect this edge using compatible available ports.",
                edge_ids=[e["id"]],
            )
    for p in resolved:
        for port in p.get("ports", []):
            if (
                port.get("required", False)
                and not used[(p["node_id"], port["name"])]
            ):
                finding(
                    "graph:required-port",
                    f"Required port {p['name']}/{port['name']} is unconnected.",
                    [p["node_id"]],
                    "dependency",
                    hint="Connect this port to a compatible opposite-direction port.",
                )
    for r in rules:
        if not r.get("enabled", True):
            continue
        try:
            validate_parameters(r["type"], r["parameters"])
        except ValueError as e:
            finding(
                r["key"],
                str(e),
                [],
                "schema",
                hint="Correct this rule in Rule Studio.",
                rule_id=r.get("id", ""),
            )
            continue
        result = evaluate(resolved, [r])
        effects.extend(result["effects"])
        if not result["findings"]:
            continue
        p, kind = r["parameters"], r["type"]
        category = "constraint"
        selector = {}
        if kind == "pairwise":
            sels = [p["a"], p["b"]]
            if p["relation"] == "require":
                category, selector = "dependency", p["b"]
        elif kind == "conditional":
            sels = [p["when"]]
            category, selector = "dependency", p["require"]
        elif kind == "exclusive":
            sels = p["members"]
            category = "exclusivity"
        elif kind == "emergent":
            sels = p["all"]
            category = "emergent-conflict"
        else:
            sels = [p["scope"]] if "scope" in p else []
            category = "quantitative"
            if "min" in p:
                scoped = [
                    n for n in resolved if not sels or matches(n, sels[0])
                ]
                metric = (
                    len(scoped)
                    if p["metric"] == "node_count"
                    else sum(
                        n["cost"]
                        if p["metric"] == "cost"
                        else n["properties"].get(p.get("property", ""), 0)
                        for n in scoped
                        if isinstance(
                            n["properties"].get(p.get("property", ""), 0),
                            (int, float),
                        )
                    )
                )
                if metric < p["min"]:
                    category = "dependency"
        affected = [
            n["node_id"]
            for n in resolved
            if not sels or any(matches(n, s) for s in sels)
        ]
        for f in result["findings"]:
            finding(
                r["key"],
                f.get("explanation", r["explanation"]),
                affected,
                category,
                f["severity"],
                r.get("repair_hint", ""),
                selector=selector,
                rule_id=r.get("id", ""),
            )
    errors = [f for f in findings if f["severity"] == "error"]
    status = (
        "invalid"
        if any(f["root_cause"] != "dependency" for f in errors)
        else "partial"
        if errors
        else "valid"
    )
    grouped = defaultdict(list)
    for f in findings:
        grouped[f["root_cause"]].append(f)
    return {
        "schema_version": 2,
        "status": status,
        "valid": status == "valid",
        "findings": findings,
        "effects": effects,
        "cost": sum(p["cost"] for p in resolved),
        "dna": [
            {
                "root_cause": key,
                "rule_ids": sorted({f["rule_id"] for f in group}),
                "node_ids": sorted({n for f in group for n in f["node_ids"]}),
                "count": len(group),
            }
            for key, group in sorted(grouped.items())
        ],
        "evaluation_scope": "live node and typed directed edge constraints",
    }


def error_signature(result: dict) -> set[tuple]:
    return {
        (f["rule_key"], f["reason"], tuple(f["node_ids"]), tuple(f["edge_ids"]))
        for f in result["findings"]
        if f["severity"] == "error"
    }


def apply_repair(graph: dict, proposal: dict) -> dict:
    result = deepcopy(graph)
    for op in proposal["operations"]:
        if op["kind"] == "remove_node":
            result["nodes"] = [
                n for n in result["nodes"] if n["id"] != op["id"]
            ]
            result["edges"] = [
                e
                for e in result["edges"]
                if op["id"] not in (e["source"], e["target"])
            ]
        elif op["kind"] == "remove_edge":
            result["edges"] = [
                e for e in result["edges"] if e["id"] != op["id"]
            ]
        elif op["kind"] == "add_node":
            result["nodes"].append(op["node"])
        elif op["kind"] == "add_edge":
            result["edges"].append(op["edge"])
    return result


def verified_repairs(
    primitives: list[dict], rules: list[dict], graph: dict, limit: int = 12
) -> list[dict]:
    baseline = evaluate_graph(primitives, rules, **graph)
    before = error_signature(baseline)
    if not before:
        return []
    candidates = []
    for n in graph["nodes"]:
        candidates.append(
            {
                "label": f"Remove node {n['id']}",
                "operations": [{"kind": "remove_node", "id": n["id"]}],
            }
        )
    for e in graph["edges"]:
        candidates.append(
            {
                "label": f"Remove edge {e['id']}",
                "operations": [{"kind": "remove_edge", "id": e["id"]}],
            }
        )
    present = {n["primitive_key"] for n in graph["nodes"]}
    for p in primitives:
        if p["key"] not in present:
            candidates.append(
                {
                    "label": f"Add {p['name']}",
                    "operations": [
                        {
                            "kind": "add_node",
                            "node": {
                                "id": f"repair-{uuid4().hex[:8]}",
                                "primitive_key": p["key"],
                                "position": {"x": 120, "y": 120},
                            },
                        }
                    ],
                }
            )
    library = {p["key"]: p for p in primitives}
    for a in graph["nodes"]:
        for b in graph["nodes"]:
            for out in library.get(a["primitive_key"], {}).get("ports", []):
                for inp in library.get(b["primitive_key"], {}).get("ports", []):
                    if (
                        a["id"] != b["id"]
                        and out["direction"] == "output"
                        and inp["direction"] == "input"
                        and out["type"] == inp["type"]
                    ):
                        candidates.append(
                            {
                                "label": f"Connect {a['id']}/{out['name']} → {b['id']}/{inp['name']}",
                                "operations": [
                                    {
                                        "kind": "add_edge",
                                        "edge": {
                                            "id": uuid4().hex,
                                            "source": a["id"],
                                            "target": b["id"],
                                            "source_port": out["name"],
                                            "target_port": inp["name"],
                                        },
                                    }
                                ],
                            }
                        )
    verified = []
    for c in candidates:
        result = evaluate_graph(primitives, rules, **apply_repair(graph, c))
        after = error_signature(result)
        if after < before:
            verified.append(
                {
                    **c,
                    "verified": True,
                    "resolved": len(before - after),
                    "remaining": len(after),
                    "status_after": result["status"],
                    "edit_count": len(c["operations"]),
                }
            )
    verified.sort(key=lambda c: (c["edit_count"], c["remaining"], c["label"]))
    return verified[:limit]


def push_history(
    undo: list[str], current: str, redo: list[str], limit: int = 50
) -> tuple[list[str], list[str]]:
    return [*undo, current][-limit:], []

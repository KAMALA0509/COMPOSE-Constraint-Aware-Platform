import reflex as rx

import math
from time import monotonic
from app.services.engine import evaluate_graph
from app.services.rule_schema import matches, validate_selector

PRESETS = {
    "Protected API": {
        "selectors": [{"keys": ["demo:edge-gateway"]}],
        "max_cost": 350,
        "max_blocks": 10,
    },
    "Observable async": {
        "selectors": [
            {"keys": ["demo:app-service"]},
            {"keys": ["demo:queue"]},
            {"keys": ["demo:worker"]},
            {"properties": {"observability": True}},
        ],
        "max_cost": 350,
        "max_blocks": 10,
    },
    "Impossible dual database": {
        "selectors": [{"keys": ["demo:postgres"]}, {"keys": ["demo:mysql"]}],
        "max_cost": 650,
        "max_blocks": 12,
    },
}


def validate_goal(goal: dict):
    allowed = {
        "selectors",
        "preferences",
        "max_cost",
        "max_blocks",
        "time_budget",
        "node_budget",
    }
    if set(goal) - allowed:
        raise ValueError("Unknown goal fields.")
    for field in ("selectors", "preferences"):
        values = goal.get(field, [])
        if not isinstance(values, list) or len(values) > 30:
            raise ValueError(
                f"{field} must be an array of at most 30 selectors."
            )
        for selector in values:
            validate_selector(selector)
    for field, default, maximum in (
        ("max_cost", 650, 1000000),
        ("max_blocks", 12, 30),
        ("time_budget", 2, 10),
        ("node_budget", 20000, 200000),
    ):
        value = goal.get(field, default)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
            or value > maximum
        ):
            raise ValueError(
                f"{field} must be finite, nonnegative and at most {maximum}."
            )
        if field in ("max_blocks", "node_budget") and not isinstance(
            value, int
        ):
            raise ValueError(f"{field} must be an integer.")


def solve(primitives: list[dict], rules: list[dict], goal: dict) -> dict:
    validate_goal(goal)
    start = monotonic()
    max_cost, max_blocks = goal.get("max_cost", 650), goal.get("max_blocks", 12)
    time_budget, node_budget = (
        goal.get("time_budget", 2),
        goal.get("node_budget", 20000),
    )
    required = goal.get("selectors", [])
    preferences = goal.get("preferences", [])
    solutions = []
    visited = 0
    exhausted = False
    domain = sorted(primitives, key=lambda p: (p["cost"], p["key"]))
    enabled = [r for r in rules if r.get("enabled", True)]

    def tick():
        nonlocal visited, exhausted
        if visited >= node_budget or monotonic() - start >= time_budget:
            exhausted = True
            return False
        visited += 1
        return True

    def wire(nodes, selected, edges):
        if not tick():
            return None
        result = evaluate_graph(primitives, rules, nodes, edges)
        port_finding = next(
            (
                f
                for f in result["findings"]
                if f["rule_key"] == "graph:required-port"
                and f["severity"] == "error"
            ),
            None,
        )
        if port_finding is None:
            return edges if result["valid"] else None
        occupied = {(e["source"], e["source_port"]) for e in edges} | {
            (e["target"], e["target_port"]) for e in edges
        }
        nid = port_finding["node_ids"][0]
        index = next(i for i, n in enumerate(nodes) if n["id"] == nid)
        port = next(
            p
            for p in selected[index].get("ports", [])
            if p.get("required") and (nid, p["name"]) not in occupied
        )
        for j, other in enumerate(selected):
            if j == index:
                continue
            for peer in other.get("ports", []):
                if (
                    peer["type"] != port["type"]
                    or peer["direction"] == port["direction"]
                ):
                    continue
                if (nodes[j]["id"], peer["name"]) in occupied and not peer.get(
                    "multiple", False
                ):
                    continue
                source, target = (
                    (nodes[index], nodes[j])
                    if port["direction"] == "output"
                    else (nodes[j], nodes[index])
                )
                out, inp = (
                    (port, peer)
                    if port["direction"] == "output"
                    else (peer, port)
                )
                e = {
                    "id": f"s{len(edges)}",
                    "source": source["id"],
                    "target": target["id"],
                    "source_port": out["name"],
                    "target_port": inp["name"],
                }
                found = wire(nodes, selected, [*edges, e])
                if found is not None:
                    return found
                if exhausted:
                    return None
        return None

    def walk(chosen: set[int], available: set[int]):
        if not tick():
            return
        # Propagate requirements with a single remaining candidate to a fixed point.
        while True:
            selected = [domain[i] for i in sorted(chosen)]
            constraints = list(required)
            for r in enabled:
                p = r["parameters"]
                if r["type"] == "conditional" and any(
                    matches(n, p["when"]) for n in selected
                ):
                    if r["severity"] == "error":
                        constraints.append(p["require"])
                elif (
                    r["type"] == "pairwise"
                    and p["relation"] == "require"
                    and r["severity"] == "error"
                    and any(matches(n, p["a"]) for n in selected)
                ):
                    constraints.append(p["b"])
            forced = set()
            for selector in constraints:
                if any(matches(n, selector) for n in selected):
                    continue
                candidates = {
                    i for i in available if matches(domain[i], selector)
                }
                if not candidates:
                    return
                if len(candidates) == 1:
                    forced.update(candidates)
            if not forced:
                break
            chosen, available = chosen | forced, available - forced
        if (
            len(chosen) > max_blocks
            or sum(n["cost"] for n in selected) > max_cost
        ):
            return
        nodes = [
            {
                "id": f"n{i}",
                "primitive_key": p["key"],
                "position": {"x": (i % 4) * 260, "y": (i // 4) * 150},
            }
            for i, p in enumerate(selected)
        ]
        # Only genuinely monotone conflicts prune an incomplete branch.
        for r in enabled:
            p = r["parameters"]
            monotone = (
                r["type"] == "exclusive"
                or (r["type"] == "pairwise" and p["relation"] == "exclude")
                or (r["type"] == "emergent" and p.get("outcome") == "conflict")
                or (
                    r["type"] == "quantitative"
                    and p["metric"] in ("cost", "node_count")
                    and "max" in p
                )
            )
            if monotone and r["severity"] == "error":
                check = (
                    {
                        **r,
                        "parameters": {
                            k: v for k, v in p.items() if k != "min"
                        },
                    }
                    if r["type"] == "quantitative"
                    else r
                )
                if (
                    evaluate_graph(primitives, [check], nodes, [])["status"]
                    == "invalid"
                ):
                    return
        if not available or len(chosen) == max_blocks:
            if not all(any(matches(p, s) for p in selected) for s in required):
                return
            edges = wire(nodes, selected, [])
            if edges is not None:
                evaluation = evaluate_graph(primitives, rules, nodes, edges)
                cost = evaluation["cost"]
                preferred = sum(
                    any(matches(p, s) for p in selected) for s in preferences
                )
                warnings = sum(
                    f["severity"] == "warning" for f in evaluation["findings"]
                )
                solutions.append(
                    {
                        "nodes": nodes,
                        "edges": edges,
                        "validation": evaluation,
                        "cost": cost,
                        "preferred": preferred,
                        "warnings": warnings,
                        "blocks": len(nodes),
                    }
                )
                solutions.sort(
                    key=lambda s: (
                        -s["preferred"],
                        s["warnings"],
                        s["cost"],
                        s["blocks"],
                    )
                )
                del solutions[10:]
            return
        next_index = min(available)
        rest = available - {next_index}
        walk(chosen, rest)
        if not exhausted:
            walk(chosen | {next_index}, rest)

    walk(set(), set(range(len(domain))))
    status = (
        "budget-exhausted"
        if exhausted
        else "solved"
        if solutions
        else "proven-impossible"
    )
    return {
        "status": status,
        "solutions": solutions,
        "visited": visited,
        "elapsed_ms": round((monotonic() - start) * 1000, 1),
        "complete": not exhausted,
        "reason": "Budget reached; any returned candidates are verified but rankings are provisional."
        if exhausted
        else "Exhaustive bounded search completed."
        if solutions
        else "No valid graph exists within this library, selector, cost and block domain.",
        "domain": "At most one occurrence of each library primitive; directed typed edges satisfy required ports. Optional edges are omitted.",
    }

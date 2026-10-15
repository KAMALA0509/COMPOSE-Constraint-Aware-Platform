import reflex as rx

import json
import pytest
from fastapi.testclient import TestClient
from app.services.demo import demo_primitives, demo_rules
from app.services.engine import (
    evaluate_graph,
    verified_repairs,
    apply_repair,
    error_signature,
    push_history,
)
from app.services.solver import solve, PRESETS
from app.services.api import api


def graph(keys):
    return {
        "nodes": [
            {
                "id": f"n{i}",
                "primitive_key": f"demo:{key}",
                "position": {"x": i * 100, "y": 0},
            }
            for i, key in enumerate(keys)
        ],
        "edges": [],
    }


def test_partial_invalid_valid():
    p, r = demo_primitives(), demo_rules()
    assert (
        evaluate_graph(p, r, **graph(["edge-gateway"]))["status"] == "partial"
    )
    assert (
        evaluate_graph(p, r, **graph(["postgres", "mysql"]))["status"]
        == "invalid"
    )
    assert (
        evaluate_graph(
            p, r, **graph(["edge-gateway", "identity", "waf", "metrics"])
        )["status"]
        == "valid"
    )


def test_three_way_and_verified_repair():
    p = demo_primitives()
    r = [
        rule
        for rule in demo_rules()
        if rule["key"] == "demo:rule:three-way-ingress"
    ]
    g = graph(["edge-gateway", "load-balancer", "service-mesh"])
    result = evaluate_graph(p, r, **g)
    assert result["status"] == "invalid"
    assert len(result["findings"][0]["node_ids"]) == 3
    for i in range(3):
        assert evaluate_graph(
            p,
            r,
            nodes=[n for j, n in enumerate(g["nodes"]) if i != j],
            edges=[],
        )["valid"]
    repairs = verified_repairs(p, r, g)
    assert repairs and repairs[0]["edit_count"] == 1
    for proposal in repairs:
        assert error_signature(
            evaluate_graph(p, r, **apply_repair(g, proposal))
        ) < error_signature(result)
    assert g == graph(["edge-gateway", "load-balancer", "service-mesh"])
    assert result["dna"][0]["root_cause"] == "emergent-conflict"


def test_typed_direction_multiplicity_required_and_unknown():
    p = demo_primitives()
    g = graph(["edge-gateway", "waf", "postgres"])
    good = {
        "id": "e",
        "source": "n0",
        "target": "n1",
        "source_port": "out",
        "target_port": "in",
    }
    assert evaluate_graph(p, [], g["nodes"], [good])["valid"]
    for bad in [
        {**good, "target": "n2"},
        {**good, "source_port": "in"},
        {**good, "target": "missing"},
        {**good, "target_port": "missing"},
    ]:
        assert evaluate_graph(p, [], g["nodes"], [bad])["status"] == "invalid"
    assert (
        evaluate_graph(p, [], g["nodes"], [good, {**good, "id": "e2"}])[
            "status"
        ]
        == "invalid"
    )
    p[0]["ports"][0]["required"] = True
    assert (
        evaluate_graph(p, [], **graph(["edge-gateway"]))["status"] == "partial"
    )
    assert (
        evaluate_graph(
            p, [], nodes=[{"id": "x", "primitive_key": "absent"}], edges=[]
        )["status"]
        == "invalid"
    )


@pytest.mark.parametrize(
    "kind,params,keys,status",
    [
        (
            "pairwise",
            {
                "a": {"category": "Compute"},
                "b": {"category": "Operations"},
                "relation": "require",
            },
            ["app-service"],
            "partial",
        ),
        (
            "pairwise",
            {
                "a": {"keys": ["demo:postgres"]},
                "b": {"keys": ["demo:mysql"]},
                "relation": "exclude",
            },
            ["postgres", "mysql"],
            "invalid",
        ),
        (
            "conditional",
            {
                "when": {"category": "Compute"},
                "require": {"category": "Operations"},
            },
            ["worker"],
            "partial",
        ),
        (
            "exclusive",
            {
                "members": [{"category": "Data"}, {"category": "Compute"}],
                "max_count": 1,
            },
            ["postgres", "worker"],
            "invalid",
        ),
        ("quantitative", {"metric": "cost", "max": 1}, ["postgres"], "invalid"),
        (
            "quantitative",
            {"metric": "node_count", "min": 2},
            ["postgres"],
            "partial",
        ),
        (
            "quantitative",
            {"metric": "property", "property": "database", "max": 2},
            ["postgres"],
            "invalid",
        ),
        (
            "emergent",
            {
                "all": [{"category": "Data"}, {"category": "Compute"}],
                "effect": "Combined",
            },
            ["postgres", "worker"],
            "valid",
        ),
    ],
)
def test_rule_types(kind, params, keys, status):
    r = {
        "key": "test",
        "id": 42,
        "name": "Test rule",
        "type": kind,
        "enabled": True,
        "severity": "error",
        "parameters": params,
        "explanation": "Test constraint",
        "repair_hint": "Adjust composition",
    }
    result = evaluate_graph(demo_primitives(), [r], **graph(keys))
    assert result["status"] == status
    if result["findings"]:
        assert result["findings"][0]["rule_id"] == "42"


def test_search_presets_and_budget():
    p, r = demo_primitives(), demo_rules()
    for name in ("Protected API", "Observable async"):
        result = solve(
            p, r, {**PRESETS[name], "node_budget": 500, "time_budget": 3}
        )
        assert result["solutions"]
        for s in result["solutions"]:
            assert evaluate_graph(p, r, s["nodes"], s["edges"])["valid"]
    impossible = solve(p, r, PRESETS["Impossible dual database"])
    assert (
        impossible["status"] == "proven-impossible"
        and not impossible["solutions"]
    )
    assert solve(p, r, {"node_budget": 0})["status"] == "budget-exhausted"
    assert (
        solve(p, r, {"selectors": [{"keys": ["not-in-library"]}]})["status"]
        == "proven-impossible"
    )


def test_undo_redo_snapshot_and_branch():
    undo, redo = push_history([], json.dumps(graph([])), [])
    current = json.dumps(graph(["worker"]))
    redo.append(current)
    previous = undo.pop()
    assert json.loads(previous) == graph([])
    undo.append(previous)
    assert json.loads(redo.pop()) == graph(["worker"])
    undo, redo = push_history(undo, current, [previous])
    assert not redo and undo[-1] == current


def test_api_validation(monkeypatch):
    monkeypatch.setattr(
        "app.services.api.read_workspace",
        lambda: {
            "primitives": demo_primitives(),
            "rules": demo_rules(),
            "saved": [],
        },
    )
    with TestClient(api) as client:
        assert client.get("/api/primitives").status_code == 200
        assert client.get("/api/compositions/missing").status_code == 404
        response = client.post("/api/validate", json=graph(["edge-gateway"]))
        assert (
            response.status_code == 200
            and response.json()["status"] == "partial"
        )
        response = client.post(
            "/api/validate", json={"nodes": [{"primitive_key": "bad"}]}
        )
        assert (
            response.status_code == 422
            and response.json()["error"]["code"] == "invalid_body"
        )
        assert (
            client.post("/api/solve", json={"max_cost": -1}).status_code == 422
        )
        assert (
            client.post("/api/solve", json={"selectors": [{}]}).status_code
            == 422
        )

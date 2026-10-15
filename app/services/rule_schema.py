import reflex as rx

import json
import math
from itertools import combinations

from app.models import JSONValue

RULE_TYPES = (
    "pairwise",
    "conditional",
    "exclusive",
    "quantitative",
    "emergent",
)


def parse_json(text: str, expected: type, label: str):
    def reject(value: str):
        raise ValueError(f"{label}: {value} is not a finite JSON value.")

    try:
        value = json.loads(text, parse_constant=reject)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{label}: invalid JSON at line {error.lineno}, column {error.colno}."
        ) from error
    if not isinstance(value, expected):
        raise ValueError(
            f"{label} must be a JSON {'object' if expected is dict else 'array'}."
        )
    return value


def validate_ports(ports: list[dict[str, JSONValue]]) -> None:
    names: set[str] = set()
    for port in ports:
        if not isinstance(port, dict) or set(port) - {
            "name",
            "direction",
            "type",
            "required",
            "multiple",
        }:
            raise ValueError(
                "Each port needs name, direction and type; optional keys: required, multiple."
            )
        name = port.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError(
                "Port names must be nonempty and unique within a primitive."
            )
        names.add(name)
        if port.get("direction") not in ("input", "output"):
            raise ValueError(f"Port {name}: direction must be input or output.")
        if (
            not isinstance(port.get("type"), str)
            or not str(port["type"]).strip()
        ):
            raise ValueError(
                f"Port {name}: type must be a nonempty string (e.g. http, sql, event)."
            )
        for flag in ("required", "multiple"):
            if flag in port and not isinstance(port[flag], bool):
                raise ValueError(f"Port {name}: {flag} must be boolean.")


def validate_selector(
    selector: object, known_keys: set[str] | None = None
) -> None:
    if (
        not isinstance(selector, dict)
        or not selector
        or set(selector) - {"keys", "category", "properties"}
    ):
        raise ValueError(
            "A selector must contain keys, category and/or properties. Unknown selector fields are not allowed."
        )
    if "keys" in selector:
        keys = selector["keys"]
        if (
            not isinstance(keys, list)
            or not keys
            or any(not isinstance(key, str) or not key for key in keys)
        ):
            raise ValueError(
                "Selector keys must be a nonempty array of primitive key strings."
            )
        if known_keys is not None and set(keys) - known_keys:
            raise ValueError(
                f"Unknown primitive keys: {', '.join(sorted(set(keys) - known_keys))}."
            )
    if "category" in selector and (
        not isinstance(selector["category"], str)
        or not selector["category"].strip()
    ):
        raise ValueError("Selector category must be a nonempty string.")
    if "properties" in selector and (
        not isinstance(selector["properties"], dict)
        or not selector["properties"]
    ):
        raise ValueError(
            "Selector properties must be a nonempty object of exact-match property values."
        )


def validate_parameters(
    kind: str, params: dict[str, JSONValue], known_keys: set[str] | None = None
) -> None:
    fields = {
        "pairwise": {"a", "b", "relation"},
        "conditional": {"when", "require"},
        "exclusive": {"members", "max_count"},
        "quantitative": {"metric", "property", "scope", "min", "max"},
        "emergent": {"all", "effect", "outcome"},
    }
    if kind not in fields:
        raise ValueError("Choose one of the five supported rule types.")
    if set(params) - fields[kind]:
        raise ValueError(
            f"Unknown parameters for {kind}: {', '.join(sorted(set(params) - fields[kind]))}."
        )
    if kind == "pairwise":
        validate_selector(params.get("a"), known_keys)
        validate_selector(params.get("b"), known_keys)
        if params.get("relation") not in ("require", "exclude"):
            raise ValueError("Pairwise relation must be require or exclude.")
    elif kind == "conditional":
        validate_selector(params.get("when"), known_keys)
        validate_selector(params.get("require"), known_keys)
    elif kind in ("exclusive", "emergent"):
        selectors = params.get("members" if kind == "exclusive" else "all")
        if not isinstance(selectors, list) or len(selectors) < 2:
            raise ValueError("Provide at least two selectors.")
        for selector in selectors:
            validate_selector(selector, known_keys)
        if kind == "exclusive":
            count = params.get("max_count")
            if (
                isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
            ):
                raise ValueError("max_count must be a nonnegative integer.")
        elif (
            not isinstance(params.get("effect"), str)
            or not str(params["effect"]).strip()
        ):
            raise ValueError(
                "An emergent rule needs a nonempty effect description."
            )
        if kind == "emergent" and params.get("outcome", "capability") not in (
            "capability",
            "conflict",
        ):
            raise ValueError("Emergent outcome must be capability or conflict.")
    else:
        if params.get("metric") not in ("cost", "node_count", "property"):
            raise ValueError("metric must be cost, node_count or property.")
        if params["metric"] == "property" and (
            not isinstance(params.get("property"), str)
            or not str(params["property"]).strip()
        ):
            raise ValueError("A property metric needs a property name.")
        if params["metric"] != "property" and "property" in params:
            raise ValueError("property is only allowed with metric=property.")
        if "scope" in params:
            validate_selector(params["scope"], known_keys)
        if "min" not in params and "max" not in params:
            raise ValueError("Provide min and/or max.")
        for bound in ("min", "max"):
            if bound in params and (
                isinstance(params[bound], bool)
                or not isinstance(params[bound], (float, int))
                or not math.isfinite(params[bound])
                or params[bound] < 0
            ):
                raise ValueError(
                    f"{bound} must be a finite nonnegative number."
                )
        if params.get("min", 0) > params.get("max", math.inf):
            raise ValueError("Minimum cannot exceed maximum.")


def matches(primitive: dict, selector: dict) -> bool:
    return (
        ("keys" not in selector or primitive["key"] in selector["keys"])
        and (
            "category" not in selector
            or primitive["category"] == selector["category"]
        )
        and all(
            primitive["properties"].get(key) == value
            for key, value in selector.get("properties", {}).items()
        )
    )


def evaluate(nodes: list[dict], rules: list[dict]) -> dict:
    findings: list[dict] = []
    effects: list[str] = []
    for rule in rules:
        if not rule["enabled"]:
            continue
        params, kind = rule["parameters"], rule["type"]
        violated = False
        if kind == "pairwise":
            a = any(matches(node, params["a"]) for node in nodes)
            b = any(matches(node, params["b"]) for node in nodes)
            violated = a and (not b if params["relation"] == "require" else b)
        elif kind == "conditional":
            violated = any(
                matches(node, params["when"]) for node in nodes
            ) and not any(matches(node, params["require"]) for node in nodes)
        elif kind == "exclusive":
            violated = (
                sum(
                    any(
                        matches(node, selector)
                        for selector in params["members"]
                    )
                    for node in nodes
                )
                > params["max_count"]
            )
        elif kind == "quantitative":
            scoped = [
                node
                for node in nodes
                if "scope" not in params or matches(node, params["scope"])
            ]
            if params["metric"] == "cost":
                total = sum(node["cost"] for node in scoped)
            elif params["metric"] == "node_count":
                total = len(scoped)
            else:
                values = [
                    node["properties"].get(params["property"], 0)
                    for node in scoped
                ]
                if any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    for value in values
                ):
                    findings.append(
                        {
                            "rule_key": rule["key"],
                            "severity": "error",
                            "explanation": f"{rule['name']}: property metric is not numeric.",
                        }
                    )
                    continue
                total = sum(values)
            violated = total < params.get("min", 0) or total > params.get(
                "max", math.inf
            )
        else:
            if all(
                any(matches(node, selector) for node in nodes)
                for selector in params["all"]
            ):
                if params.get("outcome", "capability") == "conflict":
                    violated = True
                else:
                    effects.append(params["effect"])
        if violated:
            findings.append(
                {
                    "rule_key": rule["key"],
                    "severity": rule["severity"],
                    "explanation": rule["explanation"],
                    "repair_hint": rule["repair_hint"],
                }
            )
    return {
        "schema_version": 1,
        "valid": not any(item["severity"] == "error" for item in findings),
        "findings": findings,
        "effects": effects,
        "evaluation_scope": "node constraints; typed edge validation belongs to the composer",
    }


def doctor(rules: list[dict], primitives: list[dict]) -> list[str]:
    issues: list[str] = []
    enabled: list[dict] = []
    known = {item["key"] for item in primitives}
    for rule in rules:
        if not rule["enabled"]:
            continue
        try:
            validate_parameters(rule["type"], rule["parameters"], known)
            enabled.append(rule)
        except ValueError as error:
            issues.append(f"{rule['name']}: {error}")
    required: list[tuple[dict, dict, dict]] = []
    excluded: list[tuple[dict, dict, dict]] = []
    for rule in enabled:
        p = rule["parameters"]
        if rule["type"] == "conditional":
            required.append((rule, p["when"], p["require"]))
        elif rule["type"] == "pairwise":
            (required if p["relation"] == "require" else excluded).append(
                (rule, p["a"], p["b"])
            )
    for req, trigger, target in required:
        trigger_keys = {p["key"] for p in primitives if matches(p, trigger)}
        target_keys = {p["key"] for p in primitives if matches(p, target)}
        if not target_keys:
            issues.append(
                f"{req['name']}: requirement selector matches no library primitives."
            )
        for exc, a, b in excluded:
            a_keys = {p["key"] for p in primitives if matches(p, a)}
            b_keys = {p["key"] for p in primitives if matches(p, b)}
            if (
                trigger_keys
                and target_keys
                and (
                    (trigger_keys <= a_keys and target_keys <= b_keys)
                    or (trigger_keys <= b_keys and target_keys <= a_keys)
                )
            ):
                issues.append(
                    f"{req['name']} ↔ {exc['name']}: required partners are excluded. Remove or narrow one rule."
                )
    quantitative = [rule for rule in enabled if rule["type"] == "quantitative"]
    for left, right in combinations(quantitative, 2):
        a, b = left["parameters"], right["parameters"]
        signature_a = (
            a["metric"],
            a.get("property"),
            json.dumps(a.get("scope", {}), sort_keys=True),
        )
        signature_b = (
            b["metric"],
            b.get("property"),
            json.dumps(b.get("scope", {}), sort_keys=True),
        )
        if signature_a == signature_b and max(
            a.get("min", 0), b.get("min", 0)
        ) > min(a.get("max", math.inf), b.get("max", math.inf)):
            issues.append(
                f"{left['name']} ↔ {right['name']}: quantitative intervals do not overlap. Align the bounds."
            )
    return issues

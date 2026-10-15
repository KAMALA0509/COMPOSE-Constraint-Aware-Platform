import reflex as rx

import unittest

from app.services.demo import demo_primitives, demo_rules
from app.services.rule_schema import (
    doctor,
    evaluate,
    parse_json,
    validate_parameters,
    validate_ports,
)


class SchemaTests(unittest.TestCase):
    def test_demo_schema_and_counts(self):
        primitives, rules = demo_primitives(), demo_rules()
        self.assertEqual(len(primitives), 24)
        self.assertEqual(len({item["category"] for item in primitives}), 4)
        self.assertEqual(len(rules), 19)
        self.assertEqual(
            {item["type"] for item in rules},
            {
                "pairwise",
                "conditional",
                "exclusive",
                "quantitative",
                "emergent",
            },
        )
        for primitive in primitives:
            validate_ports(primitive["ports"])
        for rule in rules:
            validate_parameters(
                rule["type"],
                rule["parameters"],
                {item["key"] for item in primitives},
            )
        self.assertEqual(doctor(rules, primitives), [])

    def test_demo_outcomes_derived(self):
        primitives, rules = demo_primitives(), demo_rules()
        lookup = {
            item["key"].removeprefix("demo:"): item for item in primitives
        }
        valid = [
            lookup[key]
            for key in [
                "edge-gateway",
                "identity",
                "waf",
                "app-service",
                "postgres",
                "backup",
                "private-network",
                "secrets",
                "metrics",
            ]
        ]
        self.assertTrue(evaluate(valid, rules)["valid"])
        self.assertFalse(
            evaluate(
                [
                    lookup[key]
                    for key in ["edge-gateway", "postgres", "mysql", "worker"]
                ],
                rules,
            )["valid"]
        )
        self.assertFalse(evaluate([lookup["app-service"]], rules)["valid"])
        emergent = evaluate(
            [
                lookup[key]
                for key in [
                    "app-service",
                    "queue",
                    "worker",
                    "metrics",
                    "logging",
                    "tracing",
                ]
            ],
            rules,
        )
        self.assertTrue(emergent["valid"])
        self.assertEqual(len(emergent["effects"]), 2)
        self.assertFalse(
            evaluate(
                [node for node in valid if node["key"] != "demo:identity"],
                rules,
            )["valid"]
        )

    def test_invalid_json_ports_bounds(self):
        for value in ["[]", '{"x":NaN}', "{broken"]:
            with self.assertRaises(ValueError):
                parse_json(value, dict, "Properties")
        with self.assertRaises(ValueError):
            validate_ports(
                [{"name": "in", "direction": "sideways", "type": "http"}]
            )
        with self.assertRaises(ValueError):
            validate_ports(
                [{"name": "in", "direction": "input", "type": "http"}] * 2
            )
        with self.assertRaises(ValueError):
            validate_parameters(
                "quantitative", {"metric": "cost", "min": 100, "max": 10}
            )
        with self.assertRaises(ValueError):
            validate_parameters(
                "conditional",
                {
                    "when": {"keys": ["missing"]},
                    "require": {"category": "Data"},
                },
                set(),
            )

    def test_doctor_conflicts_and_disabled(self):
        primitives, rules = demo_primitives(), demo_rules()
        exclusion = {
            **rules[0],
            "name": "No identity",
            "key": "custom:exclude",
            "parameters": {**rules[0]["parameters"], "relation": "exclude"},
        }
        bound = {
            **rules[11],
            "name": "Large minimum budget",
            "key": "custom:bound",
            "parameters": {"metric": "cost", "min": 700},
        }
        issues = doctor([*rules, exclusion, bound], primitives)
        self.assertTrue(any("required partners" in issue for issue in issues))
        self.assertTrue(
            any("intervals do not overlap" in issue for issue in issues)
        )
        exclusion["enabled"] = False
        bound["enabled"] = False
        self.assertEqual(doctor([*rules, exclusion, bound], primitives), [])


if __name__ == "__main__":
    unittest.main()

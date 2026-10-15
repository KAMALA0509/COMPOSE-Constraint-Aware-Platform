import reflex as rx

import asyncio
import json
import logging
import math
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select

from app.models import Activity, Composition, Primitive, Rule
from app.services.demo import seed_demo
from app.services.rule_schema import (
    doctor,
    parse_json,
    validate_parameters,
    validate_ports,
)


class WorkspaceState(rx.State):
    primitives: list[dict[str, str]] = []
    rules: list[dict[str, str]] = []
    activity: list[dict[str, str]] = []
    counts: dict[str, int] = {
        "primitives": 0,
        "rules": 0,
        "enabled": 0,
        "compositions": 0,
    }
    doctor_issues: list[str] = []
    search: str = ""
    category: str = "All categories"
    rule_search: str = ""
    rule_type: str = "All types"
    loading: bool = False
    busy: bool = False
    error: str = ""
    notice: str = ""
    editor: str = ""
    edit_key: str = ""
    draft: dict[str, str] = {
        "name": "",
        "category": "Compute",
        "description": "",
        "cost": "0",
        "properties": "{}",
        "ports": "[]",
        "metadata": "{}",
        "type": "pairwise",
        "severity": "error",
        "enabled": "true",
        "parameters": '{"a":{"category":"Compute"},"b":{"category":"Operations"},"relation":"require"}',
        "explanation": "",
        "repair_hint": "",
    }
    delete_kind: str = ""
    delete_key: str = ""
    delete_name: str = ""
    reset_confirmation: bool = False
    revision: int = 0

    @rx.var
    def categories(self) -> list[str]:
        return [
            "All categories",
            *sorted({item["category"] for item in self.primitives}),
        ]

    @rx.var
    def filtered_primitives(self) -> list[dict[str, str]]:
        term = self.search.lower().strip()
        return [
            item
            for item in self.primitives
            if (
                self.category == "All categories"
                or item["category"] == self.category
            )
            and (
                not term
                or term
                in f"{item['name']} {item['description']} {item['key']}".lower()
            )
        ]

    @rx.var
    def filtered_rules(self) -> list[dict[str, str]]:
        term = self.rule_search.lower().strip()
        return [
            item
            for item in self.rules
            if (self.rule_type == "All types" or item["type"] == self.rule_type)
            and (
                not term
                or term in f"{item['name']} {item['explanation']}".lower()
            )
        ]

    @rx.event
    def change_search(self, value: str):
        self.search = value

    @rx.event
    def change_category(self, value: str):
        self.category = value

    @rx.event
    def change_rule_search(self, value: str):
        self.rule_search = value

    @rx.event
    def change_rule_type(self, value: str):
        self.rule_type = value

    def _snapshot(self) -> dict:
        with rx.session() as session:
            seed_demo(session)
            session.commit()
            primitives = session.scalars(
                select(Primitive).order_by(Primitive.category, Primitive.name)
            ).all()
            rules = session.scalars(
                select(Rule).order_by(Rule.type, Rule.name)
            ).all()
            events = session.scalars(
                select(Activity)
                .order_by(Activity.created_at.desc(), Activity.id.desc())
                .limit(12)
            ).all()
            primitive_rows = [
                {
                    "key": item.key,
                    "name": item.name,
                    "category": item.category,
                    "description": item.description,
                    "cost": f"{item.cost:.2f}",
                    "properties": json.dumps(item.properties_json, indent=2),
                    "ports": json.dumps(item.ports_json, indent=2),
                    "metadata": json.dumps(item.metadata_json, indent=2),
                    "port_count": str(len(item.ports_json)),
                }
                for item in primitives
            ]
            rule_rows = [
                {
                    "key": item.key,
                    "name": item.name,
                    "type": item.type,
                    "severity": item.severity,
                    "enabled": "true" if item.enabled else "false",
                    "parameters": json.dumps(item.parameters_json, indent=2),
                    "explanation": item.explanation,
                    "repair_hint": item.repair_hint,
                }
                for item in rules
            ]
            raw_rules = [
                {
                    "key": item.key,
                    "name": item.name,
                    "type": item.type,
                    "severity": item.severity,
                    "enabled": item.enabled,
                    "parameters": item.parameters_json,
                    "explanation": item.explanation,
                    "repair_hint": item.repair_hint,
                }
                for item in rules
            ]
            raw_primitives = [
                {
                    "key": item.key,
                    "category": item.category,
                    "properties": item.properties_json,
                }
                for item in primitives
            ]
            return {
                "primitives": primitive_rows,
                "rules": rule_rows,
                "activity": [
                    {
                        "action": item.action,
                        "entity_type": item.entity_type,
                        "detail": item.detail,
                        "time": item.created_at.strftime(
                            "%b %d, %Y · %H:%M UTC"
                        ),
                    }
                    for item in events
                ],
                "counts": {
                    "primitives": len(primitives),
                    "rules": len(rules),
                    "enabled": sum(item.enabled for item in rules),
                    "compositions": session.scalar(
                        select(func.count()).select_from(Composition)
                    )
                    or 0,
                },
                "doctor": doctor(raw_rules, raw_primitives),
            }

    def _apply_snapshot(self, data: dict):
        self.primitives = data["primitives"]
        self.rules = data["rules"]
        self.activity = data["activity"]
        self.counts = data["counts"]
        self.doctor_issues = data["doctor"]

    @rx.event(background=True)
    async def load(self):
        async with self:
            if self.busy or self.loading:
                return
            self.loading = True
            self.error = ""
        try:
            data = await asyncio.to_thread(self._snapshot)
            async with self:
                self._apply_snapshot(data)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    "Could not load the workspace. Please try Refresh again."
                )
        finally:
            async with self:
                self.loading = False

    @rx.event
    def open_editor(self, kind: str, key: str):
        self.error = ""
        self.notice = ""
        self.edit_key = key
        self.editor = kind
        defaults = {
            "name": "",
            "category": "Compute",
            "description": "",
            "cost": "0",
            "properties": "{}",
            "ports": "[]",
            "metadata": "{}",
            "type": "pairwise",
            "severity": "error",
            "enabled": "true",
            "parameters": '{"a":{"category":"Compute"},"b":{"category":"Operations"},"relation":"require"}',
            "explanation": "",
            "repair_hint": "",
        }
        rows = self.primitives if kind == "primitive" else self.rules
        existing = next((item for item in rows if item["key"] == key), {})
        self.draft = {**defaults, **existing}
        self.revision += 1

    @rx.event
    def close_editor(self):
        if not self.busy:
            self.editor = ""
            self.error = ""

    @rx.event
    def ask_delete(self, kind: str, key: str, name: str):
        self.delete_kind, self.delete_key, self.delete_name = kind, key, name
        self.error = ""

    @rx.event
    def cancel_delete(self):
        if not self.busy:
            self.delete_key = ""

    @rx.event
    def ask_reset(self):
        self.reset_confirmation = True
        self.error = ""

    @rx.event
    def cancel_reset(self):
        if not self.busy:
            self.reset_confirmation = False

    @rx.event
    def submit(self, form_data: dict[str, Any]):
        if self.busy:
            return
        self.draft = {
            **self.draft,
            **{key: str(value) for key, value in form_data.items()},
        }
        yield WorkspaceState.save_record

    def _write_record(self, kind: str, key: str, draft: dict[str, str]):
        name = draft["name"].strip()
        if not name:
            raise ValueError("Name is required.")
        with rx.session() as session:
            model = Primitive if kind == "primitive" else Rule
            record = (
                session.scalar(select(model).where(model.key == key))
                if key
                else None
            )
            if key and record is None:
                raise ValueError(
                    "This record no longer exists. Refresh the workspace."
                )
            creating = record is None
            if creating:
                record = model(key=uuid4().hex)
            if kind == "primitive":
                category = draft["category"].strip()
                if not category:
                    raise ValueError("Category is required.")
                try:
                    cost = float(draft["cost"])
                except ValueError as error:
                    raise ValueError("Cost must be a number.") from error
                if not math.isfinite(cost) or cost < 0:
                    raise ValueError("Cost must be finite and nonnegative.")
                properties = parse_json(draft["properties"], dict, "Properties")
                ports = parse_json(draft["ports"], list, "Ports")
                metadata = parse_json(draft["metadata"], dict, "Metadata")
                validate_ports(ports)
                record.category, record.description, record.cost = (
                    category,
                    draft["description"].strip(),
                    cost,
                )
                (
                    record.properties_json,
                    record.ports_json,
                    record.metadata_json,
                ) = properties, ports, metadata
            else:
                severity = draft["severity"]
                if severity not in ("error", "warning", "info"):
                    raise ValueError("Severity must be error, warning or info.")
                if draft["enabled"] not in ("true", "false"):
                    raise ValueError("Enabled must be true or false.")
                params = parse_json(
                    draft["parameters"], dict, "Rule parameters"
                )
                known_keys = set(session.scalars(select(Primitive.key)).all())
                validate_parameters(draft["type"], params, known_keys)
                if not draft["explanation"].strip():
                    raise ValueError("Provide an explanation of the rule.")
                record.type, record.severity, record.enabled = (
                    draft["type"],
                    severity,
                    draft["enabled"] == "true",
                )
                (
                    record.parameters_json,
                    record.explanation,
                    record.repair_hint,
                ) = (
                    params,
                    draft["explanation"].strip(),
                    draft["repair_hint"].strip(),
                )
            record.name = name
            session.add(record)
            session.add(
                Activity(
                    action="Created" if creating else "Updated",
                    entity_type=kind,
                    entity_key=record.key,
                    detail=name,
                )
            )
            session.commit()

    @rx.event(background=True)
    async def save_record(self):
        async with self:
            if self.busy or self.loading:
                return
            self.busy = True
            self.error = ""
            kind, key, draft = self.editor, self.edit_key, dict(self.draft)
        committed = False
        try:
            await asyncio.to_thread(self._write_record, kind, key, draft)
            committed = True
            data = await asyncio.to_thread(self._snapshot)
            async with self:
                self._apply_snapshot(data)
                self.editor = ""
                self.notice = "Record saved. The workspace is up to date."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else (
                        "Saved, but refresh failed. Refresh to see your changes."
                        if committed
                        else "Could not save. Your draft is preserved; please try again."
                    )
                )
                if committed:
                    self.editor = ""
        finally:
            async with self:
                self.busy = False

    def _delete_record(self, kind: str, key: str):
        with rx.session() as session:
            model = Primitive if kind == "primitive" else Rule
            record = session.scalar(select(model).where(model.key == key))
            if record is None:
                raise ValueError(
                    "This record has already been deleted. Refresh the workspace."
                )
            if kind == "primitive":
                for composition in session.scalars(select(Composition)).all():
                    if any(
                        node.get("primitive_key") == key
                        for node in composition.nodes_json
                    ):
                        raise ValueError(
                            f"Cannot delete: used by composition “{composition.title}”."
                        )

                def references(value: object) -> bool:
                    if isinstance(value, dict):
                        return (
                            isinstance(value.get("keys"), list)
                            and key in value["keys"]
                        ) or any(references(item) for item in value.values())
                    return isinstance(value, list) and any(
                        references(item) for item in value
                    )

                for rule in session.scalars(select(Rule)).all():
                    if references(rule.parameters_json):
                        raise ValueError(
                            f"Cannot delete: referenced by rule “{rule.name}”. Edit that rule first."
                        )
            session.add(
                Activity(
                    action="Deleted",
                    entity_type=kind,
                    entity_key=record.key,
                    detail=record.name,
                )
            )
            session.delete(record)
            session.commit()

    @rx.event(background=True)
    async def confirm_delete(self):
        async with self:
            if self.busy or self.loading or not self.delete_key:
                return
            self.busy = True
            self.error = ""
            kind, key = self.delete_kind, self.delete_key
        try:
            await asyncio.to_thread(self._delete_record, kind, key)
            async with self:
                self.delete_key = ""
                self.notice = "Record deleted."
            data = await asyncio.to_thread(self._snapshot)
            async with self:
                self._apply_snapshot(data)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = (
                    str(e)
                    if isinstance(e, ValueError)
                    else "Could not complete the delete and refresh. Refresh before trying again."
                )
        finally:
            async with self:
                self.busy = False

    def _toggle_rule(self, key: str):
        with rx.session() as session:
            record = session.scalar(select(Rule).where(Rule.key == key))
            if record is None:
                raise ValueError(
                    "Rule no longer exists. Refresh the workspace."
                )
            record.enabled = not record.enabled
            session.add(
                Activity(
                    action="Enabled" if record.enabled else "Disabled",
                    entity_type="rule",
                    entity_key=record.key,
                    detail=record.name,
                )
            )
            session.commit()

    @rx.event(background=True)
    async def toggle_rule(self, key: str):
        async with self:
            if self.busy or self.loading:
                return
            self.busy = True
            self.error = ""
        try:
            await asyncio.to_thread(self._toggle_rule, key)
            data = await asyncio.to_thread(self._snapshot)
            async with self:
                self._apply_snapshot(data)
                self.notice = "Rule status updated."
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Could not update the rule and refresh. Please refresh before retrying."
        finally:
            async with self:
                self.busy = False

    def _reset_demo(self):
        with rx.session() as session:
            seed_demo(session, replace=True)
            session.commit()

    @rx.event(background=True)
    async def reset_demo(self):
        async with self:
            if self.busy or self.loading or not self.reset_confirmation:
                return
            self.busy = True
            self.error = ""
        try:
            await asyncio.to_thread(self._reset_demo)
            async with self:
                self.reset_confirmation = False
                self.notice = (
                    "Demo records replaced. Custom records have been preserved."
                )
            data = await asyncio.to_thread(self._snapshot)
            async with self:
                self._apply_snapshot(data)
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.error = "Could not reset the demo and refresh. Please refresh before retrying."
        finally:
            async with self:
                self.busy = False

import reflex as rx

from uuid import uuid4
from sqlalchemy import select

from app.models import Primitive, Rule, Composition, Activity
from app.services.demo import seed_demo
from app.services.engine import canonical, evaluate_graph


def primitive_dict(p: Primitive) -> dict:
    return {
        "id": p.id,
        "key": p.key,
        "name": p.name,
        "category": p.category,
        "description": p.description,
        "cost": p.cost,
        "properties": p.properties_json,
        "ports": p.ports_json,
        "metadata": p.metadata_json,
    }


def rule_dict(r: Rule) -> dict:
    return {
        "id": r.id,
        "key": r.key,
        "name": r.name,
        "type": r.type,
        "severity": r.severity,
        "enabled": r.enabled,
        "parameters": r.parameters_json,
        "explanation": r.explanation,
        "repair_hint": r.repair_hint,
    }


def composition_dict(c: Composition) -> dict:
    return {
        "key": c.key,
        "title": c.title,
        "description": c.description,
        "nodes": c.nodes_json,
        "edges": c.edges_json,
        "validation": c.validation_json,
        "updated_at": c.updated_at.isoformat(),
    }


def read_workspace() -> dict:
    with rx.session() as session:
        seed_demo(session)
        session.commit()
        return {
            "primitives": [
                primitive_dict(p)
                for p in session.scalars(
                    select(Primitive).order_by(Primitive.name)
                ).all()
            ],
            "rules": [
                rule_dict(r)
                for r in session.scalars(select(Rule).order_by(Rule.id)).all()
            ],
            "saved": [
                composition_dict(c)
                for c in session.scalars(
                    select(Composition).order_by(Composition.updated_at.desc())
                ).all()
            ],
        }


def save_composition(key: str, title: str, graph: dict) -> str:
    if not title.strip():
        raise ValueError("A composition title is required.")
    with rx.session() as session:
        record = (
            session.scalar(select(Composition).where(Composition.key == key))
            if key
            else None
        )
        if key and record is None:
            raise ValueError(
                "Composition no longer exists. Save as a new composition."
            )
        record = record or Composition(key=uuid4().hex)
        graph = canonical(**graph)
        primitives = [
            primitive_dict(p) for p in session.scalars(select(Primitive)).all()
        ]
        rules = [rule_dict(r) for r in session.scalars(select(Rule)).all()]
        record.title = title.strip()[:200]
        record.nodes_json, record.edges_json = graph["nodes"], graph["edges"]
        record.validation_json = evaluate_graph(primitives, rules, **graph)
        session.add(record)
        session.add(
            Activity(
                action="Saved",
                entity_type="composition",
                entity_key=record.key,
                detail=record.title,
            )
        )
        session.commit()
        return record.key


def change_saved(key: str, title: str = "", delete: bool = False):
    with rx.session() as session:
        record = session.scalar(
            select(Composition).where(Composition.key == key)
        )
        if record is None:
            raise ValueError("Composition no longer exists.")
        if not delete and not title.strip():
            raise ValueError("A title is required.")
        session.add(
            Activity(
                action="Deleted" if delete else "Renamed",
                entity_type="composition",
                entity_key=key,
                detail=record.title,
            )
        )
        if delete:
            session.delete(record)
        else:
            record.title = title.strip()[:200]
        session.commit()

import reflex as rx

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, JSON, Text, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
)


type JSONValue = (
    str | int | float | bool | None | list[JSONValue] | dict[str, JSONValue]
)


class Base(MappedAsDataclass, DeclarativeBase, kw_only=True):
    pass


class Primitive(Base):
    __tablename__ = "primitive"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(
        Text, unique=True, default_factory=lambda: uuid4().hex
    )
    name: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    properties_json: Mapped[dict[str, JSONValue]] = mapped_column(
        JSON, default_factory=dict
    )
    ports_json: Mapped[list[dict[str, JSONValue]]] = mapped_column(
        JSON, default_factory=list
    )
    metadata_json: Mapped[dict[str, JSONValue]] = mapped_column(
        JSON, default_factory=dict
    )


class Rule(Base):
    __tablename__ = "rule"
    __table_args__ = (
        CheckConstraint(
            "type IN ('pairwise', 'conditional', 'exclusive', 'quantitative', 'emergent')",
            name="ck_rule_type",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(
        Text, unique=True, default_factory=lambda: uuid4().hex
    )
    name: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(Text, default="pairwise")
    severity: Mapped[str] = mapped_column(Text, default="error")
    enabled: Mapped[bool] = mapped_column(default=True)
    parameters_json: Mapped[dict[str, JSONValue]] = mapped_column(
        JSON, default_factory=dict
    )
    explanation: Mapped[str] = mapped_column(Text, default="")
    repair_hint: Mapped[str] = mapped_column(Text, default="")


class Composition(Base):
    __tablename__ = "composition"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    key: Mapped[str] = mapped_column(
        Text, unique=True, default_factory=lambda: uuid4().hex
    )
    title: Mapped[str] = mapped_column(Text, default="Untitled composition")
    description: Mapped[str] = mapped_column(Text, default="")
    nodes_json: Mapped[list[dict[str, JSONValue]]] = mapped_column(
        JSON, default_factory=list
    )
    edges_json: Mapped[list[dict[str, JSONValue]]] = mapped_column(
        JSON, default_factory=list
    )
    validation_json: Mapped[dict[str, JSONValue]] = mapped_column(
        JSON, default_factory=dict
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    action: Mapped[str] = mapped_column(Text, default="")
    entity_type: Mapped[str] = mapped_column(Text, default="")
    entity_key: Mapped[str] = mapped_column(Text, default="")
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

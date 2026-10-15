import reflex as rx

import asyncio
import logging
from fastapi import FastAPI, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.services.repository import read_workspace
from app.services.engine import evaluate_graph, verified_repairs
from app.services.solver import solve

api = FastAPI(
    title="COMPOSE API",
    version="1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


class PositionBody(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float = 0
    y: float = 0


class NodeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    primitive_key: str = Field(min_length=1, max_length=200)
    position: PositionBody = Field(default_factory=PositionBody)


class EdgeBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    source_port: str = Field(min_length=1)
    target_port: str = Field(min_length=1)


class GraphBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodes: list[NodeBody] = Field(default_factory=list, max_length=100)
    edges: list[EdgeBody] = Field(default_factory=list, max_length=300)


class SelectorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keys: list[str] | None = None
    category: str | None = None
    properties: dict | None = None


class GoalBody(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    selectors: list[SelectorBody] = Field(default_factory=list, max_length=30)
    preferences: list[SelectorBody] = Field(default_factory=list, max_length=30)
    max_cost: float = Field(default=650, ge=0, le=1000000)
    max_blocks: int = Field(default=12, ge=0, le=30, strict=True)
    time_budget: float = Field(default=2, ge=0, le=10)
    node_budget: int = Field(default=20000, ge=0, le=200000, strict=True)


@api.exception_handler(RequestValidationError)
async def body_error(request: Request, error: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "invalid_body",
                "message": "Request body or query is invalid.",
                "details": [
                    {"path": list(e["loc"]), "message": e["msg"]}
                    for e in error.errors()
                ],
            }
        },
    )


@api.exception_handler(ValueError)
async def semantic_error(request: Request, error: ValueError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "invalid_semantics", "message": str(error)}},
    )


@api.exception_handler(Exception)
async def server_error(request: Request, error: Exception):
    logging.exception(f"Error: {error}")
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "workspace_unavailable",
                "message": "Workspace operation failed. Please retry.",
            }
        },
    )


@api.get("/api/primitives")
async def primitives(
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)
):
    data = await asyncio.to_thread(read_workspace)
    return {
        "items": data["primitives"][offset : offset + limit],
        "total": len(data["primitives"]),
    }


@api.get("/api/rules")
async def rules(
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)
):
    data = await asyncio.to_thread(read_workspace)
    return {
        "items": data["rules"][offset : offset + limit],
        "total": len(data["rules"]),
    }


@api.get("/api/compositions")
async def compositions(
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)
):
    data = await asyncio.to_thread(read_workspace)
    return {
        "items": data["saved"][offset : offset + limit],
        "total": len(data["saved"]),
    }


@api.get("/api/compositions/{key}")
async def composition(key: str):
    data = await asyncio.to_thread(read_workspace)
    item = next((c for c in data["saved"] if c["key"] == key), None)
    if item is None:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "not_found",
                    "message": "Composition not found.",
                }
            },
        )
    return item


@api.post("/api/validate")
async def validate(body: GraphBody):
    data = await asyncio.to_thread(read_workspace)
    graph = body.model_dump()
    result = await asyncio.to_thread(
        evaluate_graph, data["primitives"], data["rules"], **graph
    )
    result["repairs"] = await asyncio.to_thread(
        verified_repairs, data["primitives"], data["rules"], graph
    )
    return result


@api.post("/api/solve")
async def solve_goal(body: GoalBody):
    data = await asyncio.to_thread(read_workspace)
    return await asyncio.to_thread(
        solve,
        data["primitives"],
        data["rules"],
        body.model_dump(exclude_none=True),
    )

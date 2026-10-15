import reflex as rx
import reflex_enterprise as rxe

import asyncio
import logging

from app.pages.dashboard import dashboard
from app.pages.primitives import primitives_page
from app.pages.rules import rules_page
from app.pages.assembly import (
    composer_page,
    conflicts_page,
    goals_page,
    saved_page,
)
from app.states.composer_state import ComposerState
from app.services.api import api
from app.services.demo import seed_demo
from app.states.workspace_state import WorkspaceState


def index() -> rx.Component:
    return dashboard()


def initialize_demo_sync():
    with rx.session() as session:
        seed_demo(session)
        session.commit()


async def initialize_demo():
    try:
        await asyncio.to_thread(initialize_demo_sync)
    except Exception as e:
        logging.exception(f"Error: {e}")
        # Route loading retries initialization and surfaces connection failures.


app = rxe.App(
    api_transformer=api,
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            cross_origin="",
        ),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.register_lifespan_task(initialize_demo)
app.add_page(
    index, route="/", title="COMPOSE · Dashboard", on_load=WorkspaceState.load
)
app.add_page(
    primitives_page,
    route="/primitives",
    title="COMPOSE · Primitive Library",
    on_load=WorkspaceState.load,
)
app.add_page(
    rules_page,
    route="/rules",
    title="COMPOSE · Rule Studio",
    on_load=WorkspaceState.load,
)
app.add_page(
    composer_page,
    route="/composer",
    title="COMPOSE · Composer",
    on_load=ComposerState.load,
)
app.add_page(
    conflicts_page,
    route="/conflicts",
    title="COMPOSE · Conflicts",
    on_load=ComposerState.load,
)
app.add_page(
    goals_page,
    route="/goals",
    title="COMPOSE · Goal-Seeking Lab",
    on_load=ComposerState.load,
)
app.add_page(
    saved_page,
    route="/saved",
    title="COMPOSE · Saved",
    on_load=ComposerState.load,
)

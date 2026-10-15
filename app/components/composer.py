import reflex as rx
import reflex_enterprise as rxe

from app.states.composer_state import ComposerState as C


def action(label: str, event: rx.EventHandler) -> rx.Component:
    return rx.el.button(
        label,
        on_click=event,
        class_name="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:border-teal-500 focus-visible:ring-2 focus-visible:ring-teal-600",
    )


@rx.memo
def primitive_node(
    data: rx.Var[dict], isConnectable: rx.Var[bool]
) -> rx.Component:
    return rx.el.div(
        rx.el.strong(
            data["label"].to(str),
            class_name="block border-b border-slate-100 p-3 text-sm text-[#14253d]",
        ),
        rx.foreach(
            data["ports"].to(list[dict[str, str | bool]]),
            lambda port: rx.el.div(
                rx.cond(
                    port["direction"].to(str) == "input",
                    rxe.flow.handle(
                        id=port["name"].to(str),
                        type="target",
                        position="left",
                        is_connectable=isConnectable,
                        class_name="!bg-teal-600",
                    ),
                    rxe.flow.handle(
                        id=port["name"].to(str),
                        type="source",
                        position="right",
                        is_connectable=isConnectable,
                        class_name="!bg-teal-600",
                    ),
                ),
                rx.el.span(
                    f"{port['name'].to(str)} · {port['type'].to(str)}",
                    class_name="text-xs text-slate-600",
                ),
                class_name=rx.cond(
                    port["direction"].to(str) == "input",
                    "relative px-4 py-2 text-left",
                    "relative px-4 py-2 text-right",
                ),
            ),
        ),
        class_name="min-w-48 rounded-xl border border-slate-300 bg-white text-slate-700",
    )


def canvas() -> rx.Component:
    return rx.el.div(
        rxe.flow(
            rxe.flow.controls(),
            rxe.flow.background(),
            nodes=C.nodes,
            edges=C.edges,
            node_types={"primitive": primitive_node},
            on_nodes_change=lambda changes: C.set_nodes(
                rxe.flow.util.apply_node_changes(C.nodes, changes)
            ),
            on_edges_change=lambda changes: C.set_edges(
                rxe.flow.util.apply_edge_changes(C.edges, changes)
            ),
            on_connect=lambda connection: C.set_edges(
                rxe.flow.util.add_edge(connection, C.edges)
            ),
            fit_view=True,
            color_mode="light",
        ),
        class_name="h-[560px] min-h-[400px] w-full rounded-xl border border-slate-200 bg-[#f7f9fb]",
    )


def composer_feedback() -> rx.Component:
    return rx.el.div(
        rx.cond(
            C.error != "",
            rx.el.p(
                C.error,
                role="alert",
                class_name="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700",
            ),
        ),
        rx.cond(
            C.notice != "",
            rx.el.p(
                C.notice, role="status", class_name="mb-4 text-sm text-teal-800"
            ),
        ),
        rx.cond(
            C.busy,
            rx.el.p(
                "Working…",
                role="status",
                class_name="mb-3 animate-pulse text-sm text-teal-700",
            ),
        ),
    )


def heading(title: str, subtitle: str) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.el.h1(title, class_name="text-3xl font-semibold text-[#14253d]"),
            rx.el.p(
                subtitle, class_name="mt-2 text-sm leading-6 text-slate-500"
            ),
        ),
        action("Refresh", C.load),
        class_name="mb-7 flex flex-wrap items-center justify-between gap-4",
    )


def validation_panel() -> rx.Component:
    return rx.el.section(
        rx.el.div(
            rx.el.h2(
                "Live validation",
                class_name="text-lg font-semibold text-[#14253d]",
            ),
            rx.el.span(
                C.status,
                class_name=rx.match(
                    C.status,
                    (
                        "invalid",
                        "w-fit rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700",
                    ),
                    (
                        "partial",
                        "w-fit rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800",
                    ),
                    "w-fit rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-700",
                ),
            ),
            class_name="flex items-center justify-between gap-3",
        ),
        rx.el.p(
            f"{C.nodes.length()} blocks · ${C.cost:.2f} monthly estimate",
            class_name="mt-3 text-sm text-slate-600",
        ),
        rx.foreach(
            C.findings,
            lambda f: rx.el.article(
                rx.el.p(
                    f"{f['severity']} · {f['root_cause']}",
                    class_name="text-xs font-semibold uppercase text-slate-500",
                ),
                rx.el.p(
                    f["reason"],
                    class_name="mt-2 text-sm font-medium text-slate-800",
                ),
                rx.el.p(
                    f"Rule {f['rule_id']} · nodes {f['nodes']}",
                    class_name="mt-2 break-all text-xs text-slate-500",
                ),
                rx.el.p(
                    f["hint"], class_name="mt-2 text-xs leading-5 text-teal-800"
                ),
                class_name="mt-3 rounded-lg border border-slate-200 bg-[#f7f9fb] p-4",
            ),
        ),
        rx.foreach(
            C.effects,
            lambda effect: rx.el.p(
                f"Capability · {effect}",
                class_name="mt-3 rounded-lg bg-teal-50 p-3 text-sm text-teal-800",
            ),
        ),
        rx.cond(
            C.findings.length() == 0,
            rx.el.p(
                "No violations in the current rule set.",
                class_name="mt-4 text-sm text-green-700",
            ),
        ),
        class_name="rounded-xl border border-slate-200 bg-white p-5",
    )


def repairs_panel() -> rx.Component:
    return rx.el.section(
        rx.el.h2(
            "Verified repairs",
            class_name="text-lg font-semibold text-[#14253d]",
        ),
        rx.el.p(
            "Smallest practical edits first. Each candidate is evaluated on a copy; it must remove errors without introducing new ones. Repairs may leave dependencies unresolved.",
            class_name="mt-2 text-xs leading-6 text-slate-500",
        ),
        rx.foreach(
            C.repairs,
            lambda p: rx.el.div(
                rx.el.p(
                    p["label"],
                    class_name="text-sm font-semibold text-slate-800",
                ),
                rx.el.p(p["detail"], class_name="mt-1 text-xs text-slate-500"),
                rx.el.button(
                    "Apply verified repair",
                    on_click=lambda: C.repair(p["index"]),
                    class_name="mt-3 rounded-lg bg-teal-600 px-3 py-2 text-xs font-semibold text-white hover:bg-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600",
                ),
                class_name="mt-3 rounded-lg border border-teal-100 bg-teal-50/40 p-4",
            ),
        ),
        rx.cond(
            C.repairs.length() == 0,
            rx.el.p(
                "No verified single-edit improvement available. Review the rule or add supporting nodes manually.",
                class_name="mt-4 text-sm text-slate-500",
            ),
        ),
        class_name="rounded-xl border border-slate-200 bg-white p-5",
    )

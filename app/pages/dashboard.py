import reflex as rx

from app.components.workspace import (
    feedback,
    page_header,
    primary_button,
    shell,
)
from app.states.workspace_state import WorkspaceState as S


def metric(label: str, key: str, icon: str, description: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.span(label, class_name="text-sm font-medium text-slate-500"),
            rx.icon(icon, class_name="h-5 w-5 text-teal-600"),
            class_name="flex items-center justify-between",
        ),
        rx.cond(
            S.loading,
            rx.el.div(
                class_name="mt-5 h-10 w-16 animate-pulse rounded-lg bg-slate-100"
            ),
            rx.el.p(
                S.counts[key],
                class_name="mt-4 text-4xl font-semibold tracking-tight text-[#14253d]",
            ),
        ),
        rx.el.p(description, class_name="mt-3 text-xs text-slate-500"),
        class_name="w-full rounded-xl border border-slate-200 bg-white p-6",
    )


def activity_row(item: dict[str, str]) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("activity", class_name="h-4 w-4 text-teal-600"),
            class_name="mt-1 rounded-lg bg-teal-50 p-2.5",
        ),
        rx.el.div(
            rx.el.p(
                rx.el.span(
                    item["action"], class_name="font-semibold text-slate-700"
                ),
                rx.el.span(
                    f" · {item['entity_type']}", class_name="text-slate-500"
                ),
                class_name="text-sm",
            ),
            rx.el.p(item["detail"], class_name="mt-1 text-sm text-slate-500"),
            class_name="min-w-0 flex-1",
        ),
        rx.el.span(
            item["time"], class_name="text-[11px] text-slate-400 sm:ml-auto"
        ),
        class_name="flex flex-wrap items-start gap-3 border-b border-slate-100 py-4 last:border-0",
    )


def quick_link(
    title: str, description: str, icon: str, href: str
) -> rx.Component:
    return rx.el.a(
        rx.el.div(
            rx.icon(icon, class_name="h-5 w-5 text-teal-600"),
            class_name="w-fit rounded-lg bg-teal-50 p-3",
        ),
        rx.el.div(
            rx.el.h3(title, class_name="text-sm font-semibold text-[#14253d]"),
            rx.el.p(
                description, class_name="mt-1 text-xs leading-5 text-slate-500"
            ),
            class_name="flex-1",
        ),
        rx.icon("arrow-up-right", class_name="h-4 w-4 text-slate-400"),
        href=href,
        class_name="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 hover:border-teal-300 focus-visible:ring-2 focus-visible:ring-teal-600",
    )


def dashboard() -> rx.Component:
    return shell(
        "Dashboard",
        rx.el.div(
            page_header(
                "Workspace overview",
                "Build with reusable primitives. Govern with clear rules. Compose with confidence.",
                primary_button("Reset demo", "rotate-ccw", S.ask_reset),
            ),
            feedback(),
            rx.el.div(
                rx.el.div(
                    rx.el.span(
                        "REFERENCE WORKSPACE",
                        class_name="w-fit rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-[10px] font-semibold tracking-wider text-teal-800",
                    ),
                    rx.el.h2(
                        "Good systems start with good building blocks.",
                        class_name="mt-4 text-2xl font-semibold tracking-tight text-[#14253d]",
                    ),
                    rx.el.p(
                        "Explore System Architecture primitives and define the constraints that make your designs reliable. All workspace records are persisted.",
                        class_name="mt-3 max-w-2xl text-sm leading-6 text-slate-500",
                    ),
                ),
                rx.el.div(
                    rx.icon("network", class_name="h-16 w-16 text-teal-600"),
                    class_name="hidden shrink-0 rounded-2xl border border-teal-100 bg-teal-50 p-7 md:block",
                ),
                class_name="mb-6 flex items-center justify-between gap-8 rounded-xl border border-slate-200 bg-white p-7",
            ),
            rx.el.div(
                metric(
                    "Primitives",
                    "primitives",
                    "boxes",
                    "Reusable architecture building blocks",
                ),
                metric(
                    "Rules",
                    "rules",
                    "list-checks",
                    "Stored constraints across five rule types",
                ),
                metric(
                    "Enabled rules",
                    "enabled",
                    "shield-check",
                    "Currently active in rule evaluation",
                ),
                metric(
                    "Compositions",
                    "compositions",
                    "workflow",
                    "Persisted architecture designs",
                ),
                class_name="mb-8 grid grid-cols-2 gap-4 xl:grid-cols-4",
            ),
            rx.el.div(
                rx.el.section(
                    rx.el.div(
                        rx.el.h2(
                            "Recent activity",
                            class_name="text-lg font-semibold text-[#14253d]",
                        ),
                        rx.el.span(
                            "Latest 12 events",
                            class_name="text-xs text-slate-400",
                        ),
                        class_name="flex items-center justify-between",
                    ),
                    rx.cond(
                        S.loading,
                        rx.el.div(
                            class_name="mt-6 h-48 animate-pulse rounded-lg bg-slate-50"
                        ),
                        rx.cond(
                            S.activity.length() > 0,
                            rx.el.div(
                                rx.foreach(S.activity, activity_row),
                                class_name="mt-3",
                            ),
                            rx.el.p(
                                "No activity yet. Create a primitive or rule to get started.",
                                class_name="py-10 text-sm text-slate-500",
                            ),
                        ),
                    ),
                    class_name="rounded-xl border border-slate-200 bg-white p-6",
                ),
                rx.el.div(
                    rx.el.h2(
                        "Keep building",
                        class_name="mb-4 text-lg font-semibold text-[#14253d]",
                    ),
                    quick_link(
                        "Primitive library",
                        "Explore components, typed ports and properties.",
                        "boxes",
                        "/primitives",
                    ),
                    quick_link(
                        "Protected stack",
                        "Load a complete reference design into the composer.",
                        "workflow",
                        "/composer?composition=demo:composition:valid",
                    ),
                    quick_link(
                        "Three-way conflict",
                        "Inspect an emergent routing conflict and verified repairs.",
                        "git-compare-arrows",
                        "/composer?composition=demo:composition:three-way",
                    ),
                    quick_link(
                        "Goal-seeking lab",
                        "Find and rank valid compositions under budgets.",
                        "target",
                        "/goals",
                    ),
                    quick_link(
                        "Rule studio",
                        "Edit constraints and check for contradictions.",
                        "list-checks",
                        "/rules",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.icon(
                                "stethoscope",
                                class_name="h-5 w-5 text-teal-600",
                            ),
                            rx.el.h3(
                                "Rule Doctor",
                                class_name="font-semibold text-[#14253d]",
                            ),
                            class_name="flex items-center gap-2",
                        ),
                        rx.el.p(
                            rx.cond(
                                S.doctor_issues.length() == 0,
                                "No detected contradictions in enabled rules.",
                                f"{S.doctor_issues.length()} potential issues need review.",
                            ),
                            class_name="mt-3 text-sm leading-6 text-slate-600",
                        ),
                        rx.el.p(
                            "Checks stored require/exclude pairs and overlapping quantitative bounds. Not a proof of global satisfiability.",
                            class_name="mt-2 text-xs leading-5 text-slate-500",
                        ),
                        class_name="rounded-xl border border-teal-200 bg-teal-50/50 p-5",
                    ),
                    class_name="flex flex-col gap-4",
                ),
                class_name="grid gap-6 xl:grid-cols-[1.6fr_1fr]",
            ),
        ),
    )

import reflex as rx

from app.components.workspace import shell
from app.components.composer import (
    action,
    canvas,
    composer_feedback,
    heading,
    validation_panel,
    repairs_panel,
)
from app.states.composer_state import ComposerState as C


def composer_page() -> rx.Component:
    return shell(
        "Composer",
        rx.el.div(
            heading(
                "Visual composer",
                "Drag nodes, connect compatible typed ports, select items and delete. Every change runs the shared backend evaluator.",
            ),
            composer_feedback(),
            rx.el.div(
                action("New", C.new_composition),
                action("Undo", C.undo),
                action("Redo", C.redo),
                action("Delete selected", C.delete_selected),
                action("Revalidate", C.validate),
                rx.el.a(
                    "Conflict explorer",
                    href="/conflicts",
                    class_name="rounded-lg bg-teal-600 px-4 py-2 text-sm text-white focus-visible:ring-2 focus-visible:ring-teal-600",
                ),
                class_name="mb-4 flex flex-wrap gap-2",
            ),
            rx.el.form(
                rx.el.label(
                    "Composition title",
                    html_for="composition-title",
                    class_name="text-sm font-medium text-slate-700",
                ),
                rx.el.input(
                    id="composition-title",
                    name="title",
                    default_value=C.title,
                    key=C.title,
                    required=True,
                    class_name="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800",
                ),
                rx.el.label(
                    rx.el.input(type="checkbox", name="save_as"),
                    " Save as new",
                    class_name="text-sm text-slate-600",
                ),
                rx.el.button(
                    "Save",
                    type="submit",
                    disabled=C.busy,
                    class_name="rounded-lg bg-teal-600 px-5 py-2 text-sm font-semibold text-white hover:bg-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
                ),
                on_submit=C.submit_save,
                class_name="mb-5 flex flex-wrap items-center gap-3",
            ),
            rx.el.div(
                rx.el.aside(
                    rx.el.h2(
                        "Add from library",
                        class_name="mb-3 font-semibold text-[#14253d]",
                    ),
                    rx.foreach(
                        C.library,
                        lambda p: rx.el.button(
                            rx.el.span(
                                p["name"],
                                class_name="text-sm font-medium text-slate-800",
                            ),
                            rx.el.span(
                                f"{p['category']} · ${p['cost']}",
                                class_name="text-xs text-slate-500",
                            ),
                            on_click=lambda: C.add_primitive(p["key"]),
                            class_name="flex w-full flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3 text-left hover:border-teal-400 focus-visible:ring-2 focus-visible:ring-teal-600",
                        ),
                    ),
                    class_name="flex max-h-[560px] flex-col gap-2 overflow-y-auto rounded-xl border border-slate-200 bg-white p-4",
                ),
                canvas(),
                class_name="grid min-w-0 gap-4 xl:grid-cols-[240px_minmax(0,1fr)]",
            ),
            rx.el.div(
                validation_panel(),
                repairs_panel(),
                class_name="mt-5 grid gap-5 xl:grid-cols-2",
            ),
            rx.el.details(
                rx.el.summary(
                    "Load a saved or seeded composition",
                    class_name="cursor-pointer font-medium text-teal-700",
                ),
                rx.foreach(
                    C.saved,
                    lambda c: rx.el.button(
                        c["title"],
                        on_click=lambda: C.open_saved(c["key"]),
                        class_name="m-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:border-teal-500 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                ),
                class_name="mt-6",
            ),
        ),
    )


def conflicts_page() -> rx.Component:
    return shell(
        "Conflicts",
        rx.el.div(
            heading(
                "Conflict explorer",
                "The same working composition, the same evaluator. Inspect grouped root causes and apply verified changes.",
            ),
            composer_feedback(),
            rx.el.a(
                "Back to composer",
                href="/composer",
                class_name="mb-5 inline-block text-sm font-semibold text-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.el.section(
                rx.el.h2(
                    "Conflict DNA",
                    class_name="text-lg font-semibold text-[#14253d]",
                ),
                rx.foreach(
                    C.dna,
                    lambda d: rx.el.div(
                        rx.el.h3(
                            f"{d['cause']} · {d['count']} finding(s)",
                            class_name="font-semibold text-slate-800",
                        ),
                        rx.el.p(
                            f"Rules: {d['rules']}",
                            class_name="mt-2 break-all text-xs text-slate-600",
                        ),
                        rx.el.p(
                            f"Affected nodes: {d['nodes']}",
                            class_name="mt-1 text-xs text-slate-500",
                        ),
                        class_name="mt-4 rounded-lg border border-slate-200 p-4",
                    ),
                ),
                rx.cond(
                    C.dna.length() == 0,
                    rx.el.p(
                        "No conflict groups in this composition.",
                        class_name="mt-3 text-sm text-slate-600",
                    ),
                ),
                class_name="mb-5 rounded-xl border border-slate-200 bg-white p-6",
            ),
            rx.el.div(
                validation_panel(),
                repairs_panel(),
                class_name="grid gap-5 xl:grid-cols-2",
            ),
        ),
    )


def goals_page() -> rx.Component:
    return shell(
        "Goals",
        rx.el.div(
            heading(
                "Goal-seeking lab",
                "Constraint propagation, exhaustive bounded backtracking and verified candidate ranking—not guessed architectures.",
            ),
            composer_feedback(),
            rx.el.div(
                action("Protected API", C.choose_preset("Protected API")),
                action("Observable async", C.choose_preset("Observable async")),
                action(
                    "Impossible dual database",
                    C.choose_preset("Impossible dual database"),
                ),
                class_name="mb-5 flex flex-wrap gap-3",
            ),
            rx.el.form(
                rx.el.label(
                    "Goal selectors, preferences and budgets (JSON)",
                    html_for="goal-json",
                    class_name="block text-sm font-semibold text-slate-700",
                ),
                rx.el.textarea(
                    id="goal-json",
                    name="goal",
                    default_value=C.goal_json,
                    key=C.goal_json,
                    rows=12,
                    class_name="mt-3 w-full rounded-lg border border-slate-300 bg-white p-4 font-mono text-sm text-slate-800 focus-visible:ring-2 focus-visible:ring-teal-600",
                ),
                rx.el.p(
                    "selectors: required selector array; preferences: optional ranked selector array. Selectors use keys/category/properties. max_cost: cost cap; max_blocks: 0–30; time_budget: seconds, 0–10; node_budget: 0–200000. Defaults: 650, 12, 2 seconds, 20000 search nodes.",
                    class_name="mt-3 text-xs leading-6 text-slate-500",
                ),
                rx.el.p(
                    "Search domain: at most one instance of each primitive. Solutions satisfy all error rules and required ports. Rankings prioritize preferences, fewer warnings, lower cost and fewer blocks. Budget-exhausted never means impossible.",
                    class_name="mt-2 text-xs leading-6 text-slate-500",
                ),
                rx.el.button(
                    rx.cond(C.busy, "Searching…", "Find valid compositions"),
                    disabled=C.busy,
                    type="submit",
                    class_name="mt-4 rounded-lg bg-teal-600 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
                ),
                on_submit=C.submit_goal,
                class_name="rounded-xl border border-slate-200 bg-white p-6",
            ),
            rx.el.p(
                C.search_result,
                role="status",
                class_name="my-5 rounded-xl border border-teal-200 bg-teal-50 p-5 text-sm leading-6 text-teal-900",
            ),
            rx.foreach(
                C.solutions,
                lambda s: rx.el.article(
                    rx.el.h2(
                        s["label"], class_name="font-semibold text-[#14253d]"
                    ),
                    rx.el.p(
                        s["detail"], class_name="mt-2 text-xs text-slate-500"
                    ),
                    rx.el.button(
                        "Open in composer",
                        on_click=lambda: C.use_solution(s["index"]),
                        class_name="mt-4 rounded-lg bg-teal-600 px-4 py-2 text-sm text-white focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    class_name="mb-3 rounded-xl border border-slate-200 bg-white p-5",
                ),
            ),
        ),
    )


def saved_page() -> rx.Component:
    return shell(
        "Saved",
        rx.el.div(
            heading(
                "Saved compositions",
                "Persisted designs and reference scenarios. Load, rename, delete or export JSON.",
            ),
            composer_feedback(),
            rx.cond(
                C.rename_key != "",
                rx.el.form(
                    rx.el.label(
                        "New title",
                        html_for="rename-title",
                        class_name="text-sm font-medium text-slate-700",
                    ),
                    rx.el.input(
                        id="rename-title",
                        name="title",
                        required=True,
                        class_name="flex-1 rounded-lg border border-slate-300 bg-white p-2 text-sm text-slate-800",
                    ),
                    rx.el.button(
                        "Rename",
                        type="submit",
                        disabled=C.busy,
                        class_name="rounded-lg bg-teal-600 px-4 py-2 text-sm text-white",
                    ),
                    on_submit=C.submit_rename,
                    class_name="mb-5 flex items-center gap-3",
                ),
            ),
            rx.foreach(
                C.saved,
                lambda c: rx.el.article(
                    rx.el.h2(
                        c["title"],
                        class_name="text-lg font-semibold text-[#14253d]",
                    ),
                    rx.el.p(
                        f"{c['blocks']} blocks · updated {c['updated']}",
                        class_name="mt-2 text-xs text-slate-500",
                    ),
                    rx.el.div(
                        action("Load", C.open_saved(c["key"])),
                        action("Rename", C.ask_rename(c["key"])),
                        action("Export JSON", C.export_saved(c["key"])),
                        rx.el.details(
                            rx.el.summary(
                                "Delete…",
                                class_name="cursor-pointer rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700",
                            ),
                            rx.el.p(
                                "Permanently delete this composition?",
                                class_name="my-2 text-xs text-red-700",
                            ),
                            rx.el.button(
                                "Confirm delete",
                                on_click=lambda: C.mutate_saved(
                                    c["key"], "", True
                                ),
                                disabled=C.busy,
                                class_name="rounded-lg bg-red-600 px-3 py-2 text-sm text-white focus-visible:ring-2 focus-visible:ring-red-600",
                            ),
                        ),
                        class_name="mt-4 flex flex-wrap items-start gap-2",
                    ),
                    key=c["key"],
                    class_name="mb-4 rounded-xl border border-slate-200 bg-white p-6",
                ),
            ),
            rx.cond(
                C.saved.length() == 0,
                rx.el.p(
                    "No saved compositions yet. Save a design from the composer.",
                    class_name="text-sm text-slate-600",
                ),
            ),
        ),
    )

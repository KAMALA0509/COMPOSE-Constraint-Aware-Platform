import reflex as rx

from app.components.workspace import (
    feedback,
    page_header,
    primary_button,
    schema_help,
    shell,
)
from app.states.workspace_state import WorkspaceState as S


def rule_card(item: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    item["type"],
                    class_name="w-fit rounded-full bg-teal-50 px-2.5 py-1 text-[11px] font-semibold text-teal-800",
                ),
                rx.el.span(
                    item["severity"],
                    class_name=rx.match(
                        item["severity"],
                        (
                            "error",
                            "w-fit rounded-full bg-red-50 px-2.5 py-1 text-[11px] font-medium text-red-700",
                        ),
                        (
                            "warning",
                            "w-fit rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-800",
                        ),
                        "w-fit rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-medium text-blue-700",
                    ),
                ),
                class_name="flex gap-2",
            ),
            rx.el.button(
                rx.icon("power", class_name="h-3.5 w-3.5"),
                rx.cond(item["enabled"] == "true", "Enabled", "Disabled"),
                on_click=lambda: S.toggle_rule(item["key"]),
                aria_label=f"Toggle {item['name']}",
                disabled=S.busy | S.loading,
                class_name=rx.cond(
                    item["enabled"] == "true",
                    "flex items-center gap-1.5 rounded-lg border border-teal-200 bg-teal-50 px-2.5 py-1.5 text-xs font-medium text-teal-800 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
                    "flex items-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-500 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
                ),
            ),
            class_name="flex flex-wrap items-center justify-between gap-3",
        ),
        rx.el.h2(
            item["name"], class_name="mt-4 text-lg font-semibold text-[#14253d]"
        ),
        rx.el.p(
            item["explanation"],
            class_name="mt-2 text-sm leading-6 text-slate-500",
        ),
        rx.cond(
            item["repair_hint"] != "",
            rx.el.div(
                rx.icon(
                    "lightbulb",
                    class_name="mt-0.5 h-3.5 w-3.5 shrink-0 text-teal-600",
                ),
                rx.el.p(
                    item["repair_hint"],
                    class_name="text-xs leading-5 text-slate-600",
                ),
                class_name="mt-4 flex gap-2 rounded-lg bg-[#f7f9fb] p-3",
            ),
        ),
        rx.el.details(
            rx.el.summary(
                "View condition parameters",
                class_name="cursor-pointer text-xs font-medium text-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.el.pre(
                item["parameters"],
                class_name="mt-3 overflow-x-auto rounded-lg bg-slate-50 p-3 text-[11px] leading-5 text-slate-600",
            ),
            class_name="my-4",
        ),
        rx.el.div(
            rx.el.code(
                item["key"],
                class_name="min-w-0 flex-1 select-all break-all text-[10px] text-slate-400",
            ),
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                "Edit",
                on_click=lambda: S.open_editor("rule", item["key"]),
                disabled=S.busy | S.loading,
                class_name="flex items-center gap-1 rounded-lg px-2 py-2 text-xs text-slate-600 hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                aria_label=f"Delete {item['name']}",
                on_click=lambda: S.ask_delete(
                    "rule", item["key"], item["name"]
                ),
                disabled=S.busy | S.loading,
                class_name="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            class_name="mt-auto flex items-center gap-2 border-t border-slate-100 pt-3",
        ),
        key=item["key"],
        class_name="flex min-w-0 flex-col rounded-xl border border-slate-200 bg-white p-5",
    )


def rules_page() -> rx.Component:
    return shell(
        "Rules",
        rx.el.div(
            page_header(
                "Rule studio",
                "Make design intent explicit with constraints, safeguards and emergent capabilities.",
                primary_button("New rule", "plus", S.open_editor("rule", "")),
            ),
            feedback(),
            rx.el.section(
                rx.el.div(
                    rx.el.div(
                        rx.icon(
                            "stethoscope", class_name="h-5 w-5 text-teal-600"
                        ),
                        rx.el.h2(
                            "Rule Doctor",
                            class_name="text-base font-semibold text-[#14253d]",
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    rx.el.span(
                        f"{S.doctor_issues.length()} detected issues",
                        class_name="w-fit rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-600",
                    ),
                    class_name="flex flex-wrap items-center justify-between gap-3",
                ),
                rx.el.p(
                    "Inspects enabled stored rules for invalid references, require/exclude contradictions, and impossible quantitative bounds. This targeted check is not a global satisfiability proof.",
                    class_name="mt-3 text-xs leading-6 text-slate-500",
                ),
                rx.cond(
                    S.loading,
                    rx.el.div(
                        class_name="mt-3 h-10 animate-pulse rounded-lg bg-slate-100"
                    ),
                    rx.cond(
                        S.doctor_issues.length() > 0,
                        rx.el.ul(
                            rx.foreach(
                                S.doctor_issues,
                                lambda issue: rx.el.li(
                                    rx.icon(
                                        "triangle-alert",
                                        class_name="mt-1 h-4 w-4 shrink-0 text-amber-700",
                                    ),
                                    issue,
                                    class_name="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-900",
                                ),
                            ),
                            class_name="mt-4 flex flex-col gap-2",
                        ),
                        rx.el.p(
                            rx.icon(
                                "circle-check",
                                class_name="h-4 w-4 text-teal-600",
                            ),
                            "No contradictions detected in the current enabled rules.",
                            class_name="mt-4 flex items-center gap-2 text-sm text-teal-800",
                        ),
                    ),
                ),
                class_name="mb-5 rounded-xl border border-slate-200 bg-white p-5",
            ),
            schema_help(),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Search rules",
                        html_for="rule-search",
                        class_name="sr-only",
                    ),
                    rx.icon(
                        "search",
                        class_name="absolute left-3 top-3 h-4 w-4 text-slate-400",
                    ),
                    rx.el.input(
                        id="rule-search",
                        placeholder="Search rules or explanations…",
                        default_value=S.rule_search,
                        on_change=S.change_rule_search.debounce(500),
                        class_name="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-3 text-sm text-slate-700 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    class_name="relative w-full sm:max-w-md",
                ),
                rx.el.div(
                    rx.el.label(
                        "Filter by rule type",
                        html_for="type-filter",
                        class_name="sr-only",
                    ),
                    rx.el.select(
                        rx.foreach(
                            [
                                "All types",
                                "pairwise",
                                "conditional",
                                "exclusive",
                                "quantitative",
                                "emergent",
                            ],
                            lambda kind: rx.el.option(kind, value=kind),
                        ),
                        id="type-filter",
                        value=S.rule_type,
                        on_change=S.change_rule_type,
                        class_name="w-full appearance-none rounded-lg border border-slate-200 bg-white py-2.5 pl-3 pr-10 text-sm text-slate-700 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-slate-400",
                    ),
                    class_name="relative w-full sm:w-48",
                ),
                rx.el.span(
                    f"{S.filtered_rules.length()} rules",
                    class_name="text-xs text-slate-500 sm:ml-auto",
                ),
                class_name="my-6 flex flex-wrap items-center gap-3",
            ),
            rx.cond(
                S.loading,
                rx.el.div(
                    class_name="h-64 w-full animate-pulse rounded-xl bg-slate-100"
                ),
                rx.cond(
                    S.filtered_rules.length() > 0,
                    rx.el.div(
                        rx.foreach(S.filtered_rules, rule_card),
                        class_name="grid w-full gap-5 md:grid-cols-2 2xl:grid-cols-3",
                    ),
                    rx.el.div(
                        rx.icon(
                            "list-checks",
                            class_name="mx-auto h-9 w-9 text-slate-400",
                        ),
                        rx.el.h2(
                            "No matching rules",
                            class_name="mt-4 text-lg font-semibold text-[#14253d]",
                        ),
                        rx.el.p(
                            "Adjust your filters or create a new rule.",
                            class_name="mt-2 text-sm text-slate-500",
                        ),
                        class_name="rounded-xl border border-dashed border-slate-300 bg-white p-16 text-center",
                    ),
                ),
            ),
        ),
    )

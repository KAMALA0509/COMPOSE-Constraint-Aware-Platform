import reflex as rx

from app.components.workspace import (
    feedback,
    page_header,
    primary_button,
    shell,
)
from app.states.workspace_state import WorkspaceState as S


def primitive_card(item: dict[str, str]) -> rx.Component:
    return rx.el.article(
        rx.el.div(
            rx.el.div(
                rx.icon("box", class_name="h-5 w-5 text-teal-600"),
                class_name="w-fit rounded-lg bg-teal-50 p-3",
            ),
            rx.el.span(
                item["category"],
                class_name="w-fit rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-medium text-slate-600",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.el.h2(
            item["name"], class_name="mt-5 text-lg font-semibold text-[#14253d]"
        ),
        rx.el.p(
            item["description"],
            class_name="mt-2 min-h-12 text-sm leading-6 text-slate-500",
        ),
        rx.el.div(
            rx.el.span(
                f"${item['cost']} / month",
                class_name="font-semibold text-slate-700",
            ),
            rx.el.span(
                f"{item['port_count']} typed ports", class_name="text-slate-500"
            ),
            class_name="mt-5 flex flex-wrap items-center justify-between gap-2 text-xs",
        ),
        rx.el.details(
            rx.el.summary(
                "Properties, ports & metadata",
                class_name="cursor-pointer text-xs font-medium text-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.el.p(
                "Properties",
                class_name="mt-3 text-xs font-semibold text-slate-600",
            ),
            rx.el.pre(
                item["properties"],
                class_name="mt-1 overflow-x-auto rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600",
            ),
            rx.el.p(
                "Typed ports",
                class_name="mt-3 text-xs font-semibold text-slate-600",
            ),
            rx.el.pre(
                item["ports"],
                class_name="mt-1 overflow-x-auto rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600",
            ),
            rx.el.p(
                "Metadata",
                class_name="mt-3 text-xs font-semibold text-slate-600",
            ),
            rx.el.pre(
                item["metadata"],
                class_name="mt-1 overflow-x-auto rounded-lg bg-slate-50 p-3 text-[11px] text-slate-600",
            ),
            class_name="mt-4",
        ),
        rx.el.div(
            rx.el.code(
                item["key"],
                title="Stable primitive key for rule selectors",
                class_name="min-w-0 flex-1 select-all break-all text-[10px] text-slate-400",
            ),
            rx.el.button(
                rx.icon("pencil", class_name="h-4 w-4"),
                "Edit",
                on_click=lambda: S.open_editor("primitive", item["key"]),
                disabled=S.busy | S.loading,
                class_name="flex items-center gap-1 rounded-lg px-2 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.el.button(
                rx.icon("trash-2", class_name="h-4 w-4"),
                aria_label=f"Delete {item['name']}",
                on_click=lambda: S.ask_delete(
                    "primitive", item["key"], item["name"]
                ),
                disabled=S.busy | S.loading,
                class_name="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            class_name="mt-auto flex items-center gap-2 border-t border-slate-100 pt-4",
        ),
        key=item["key"],
        class_name="flex min-w-0 flex-col gap-1 rounded-xl border border-slate-200 bg-white p-5 transition-colors hover:border-slate-300",
    )


def primitives_page() -> rx.Component:
    return shell(
        "Primitives",
        rx.el.div(
            page_header(
                "Primitive library",
                "Reusable components with properties, cost estimates and typed connection ports.",
                primary_button(
                    "New primitive", "plus", S.open_editor("primitive", "")
                ),
            ),
            feedback(),
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Search primitives",
                        html_for="primitive-search",
                        class_name="sr-only",
                    ),
                    rx.icon(
                        "search",
                        class_name="absolute left-3 top-3 h-4 w-4 text-slate-400",
                    ),
                    rx.el.input(
                        id="primitive-search",
                        placeholder="Search name, description or key…",
                        default_value=S.search,
                        on_change=S.change_search.debounce(500),
                        class_name="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm text-slate-700 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    class_name="relative w-full sm:max-w-md",
                ),
                rx.el.div(
                    rx.el.label(
                        "Filter by category",
                        html_for="category-filter",
                        class_name="sr-only",
                    ),
                    rx.el.select(
                        rx.foreach(
                            S.categories,
                            lambda category: rx.el.option(
                                category, value=category
                            ),
                        ),
                        id="category-filter",
                        value=S.category,
                        on_change=S.change_category,
                        class_name="w-full appearance-none rounded-lg border border-slate-200 bg-white py-2.5 pl-3 pr-10 text-sm text-slate-700 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    rx.icon(
                        "chevron-down",
                        class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-slate-400",
                    ),
                    class_name="relative w-full sm:w-48",
                ),
                rx.el.p(
                    f"{S.filtered_primitives.length()} components",
                    class_name="text-xs text-slate-500 sm:ml-auto",
                ),
                class_name="mb-6 flex flex-wrap items-center gap-3",
            ),
            rx.cond(
                S.loading,
                rx.el.div(
                    class_name="h-64 w-full animate-pulse rounded-xl border border-slate-200 bg-slate-100"
                ),
                rx.cond(
                    S.filtered_primitives.length() > 0,
                    rx.el.div(
                        rx.foreach(S.filtered_primitives, primitive_card),
                        class_name="grid w-full gap-5 md:grid-cols-2 2xl:grid-cols-3",
                    ),
                    rx.el.div(
                        rx.icon(
                            "search-x",
                            class_name="mx-auto h-9 w-9 text-slate-400",
                        ),
                        rx.el.h2(
                            "No matching primitives",
                            class_name="mt-4 text-lg font-semibold text-[#14253d]",
                        ),
                        rx.el.p(
                            "Try another search or category, or create your first primitive.",
                            class_name="mt-2 text-sm text-slate-500",
                        ),
                        class_name="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center",
                    ),
                ),
            ),
        ),
    )

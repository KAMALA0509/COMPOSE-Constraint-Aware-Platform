import reflex as rx

from app.states.workspace_state import WorkspaceState as S


def nav_link(label: str, icon: str, href: str, active: str) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="h-4 w-4 shrink-0"),
        label,
        href=href,
        class_name=rx.cond(
            active == label,
            "flex items-center gap-3 rounded-lg bg-white/10 px-4 py-3 text-sm font-semibold text-white focus-visible:ring-2 focus-visible:ring-teal-400",
            "flex items-center gap-3 rounded-lg px-4 py-3 text-sm text-slate-300 hover:bg-white/5 hover:text-white focus-visible:ring-2 focus-visible:ring-teal-400",
        ),
    )


def navigation(active: str) -> rx.Component:
    return rx.el.aside(
        rx.el.a(
            rx.el.div(
                rx.icon("blocks", class_name="h-6 w-6 text-teal-300"),
                class_name="rounded-xl bg-white/10 p-2",
            ),
            rx.el.div(
                rx.el.span(
                    "COMPOSE",
                    class_name="block text-lg font-semibold tracking-[0.16em] text-white",
                ),
                rx.el.span(
                    "Assembly platform", class_name="text-xs text-slate-400"
                ),
            ),
            href="/",
            class_name="flex shrink-0 items-center gap-3 px-6 py-7 focus-visible:ring-2 focus-visible:ring-teal-400",
        ),
        rx.el.nav(
            rx.el.p(
                "WORKSPACE",
                class_name="mb-3 px-4 text-[10px] font-semibold tracking-[0.18em] text-slate-400",
            ),
            nav_link("Dashboard", "layout-dashboard", "/", active),
            nav_link("Primitives", "boxes", "/primitives", active),
            nav_link("Rules", "list-checks", "/rules", active),
            rx.el.div(class_name="my-5 border-t border-white/10"),
            nav_link("Composer", "workflow", "/composer", active),
            nav_link("Conflicts", "git-compare-arrows", "/conflicts", active),
            nav_link("Goals", "target", "/goals", active),
            nav_link("Saved", "bookmark", "/saved", active),
            class_name="min-h-0 flex-1 overflow-y-auto px-3",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("network", class_name="h-4 w-4 text-teal-300"),
                rx.el.span(
                    "System Architecture",
                    class_name="text-xs font-medium text-slate-200",
                ),
                class_name="flex items-center gap-2",
            ),
            rx.el.p(
                "Reference workspace · Demo ready",
                class_name="mt-2 text-[11px] text-slate-400",
            ),
            class_name="m-4 rounded-xl border border-white/10 p-4",
        ),
        class_name="hidden h-full w-64 shrink-0 flex-col bg-[#14253d] lg:flex",
    )


def mobile_navigation(active: str) -> rx.Component:
    return rx.el.header(
        rx.el.div(
            rx.icon("blocks", class_name="h-5 w-5 text-teal-300"),
            rx.el.span(
                "COMPOSE", class_name="font-semibold tracking-widest text-white"
            ),
            class_name="flex items-center gap-2 px-4 pt-4",
        ),
        rx.el.nav(
            nav_link("Dashboard", "layout-dashboard", "/", active),
            nav_link("Primitives", "boxes", "/primitives", active),
            nav_link("Rules", "list-checks", "/rules", active),
            nav_link("Composer", "workflow", "/composer", active),
            nav_link("Conflicts", "git-compare-arrows", "/conflicts", active),
            nav_link("Goals", "target", "/goals", active),
            nav_link("Saved", "bookmark", "/saved", active),
            class_name="flex gap-1 overflow-x-auto p-2",
        ),
        class_name="shrink-0 bg-[#14253d] lg:hidden",
    )


def primary_button(
    label: str, icon: str, event: rx.EventHandler
) -> rx.Component:
    return rx.el.button(
        rx.icon(icon, class_name="h-4 w-4"),
        label,
        on_click=event,
        disabled=S.busy | S.loading,
        class_name="inline-flex items-center justify-center gap-2 rounded-lg bg-[#0d9488] px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 disabled:opacity-50",
    )


def feedback() -> rx.Component:
    return rx.el.div(
        rx.cond(
            S.error != "",
            rx.el.div(
                rx.icon("circle-alert", class_name="h-4 w-4 shrink-0"),
                S.error,
                role="alert",
                class_name="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700",
            ),
        ),
        rx.cond(
            S.notice != "",
            rx.el.div(
                rx.icon("circle-check", class_name="h-4 w-4 shrink-0"),
                S.notice,
                role="status",
                class_name="mb-4 flex items-start gap-2 rounded-lg border border-teal-200 bg-teal-50 p-4 text-sm text-teal-800",
            ),
        ),
    )


def page_header(
    title: str, subtitle: str, action: rx.Component
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                "SYSTEM ARCHITECTURE / WORKSPACE",
                class_name="mb-2 text-[10px] font-semibold tracking-[0.15em] text-slate-500",
            ),
            rx.el.h1(
                title,
                class_name="text-3xl font-semibold tracking-tight text-[#14253d]",
            ),
            rx.el.p(
                subtitle, class_name="mt-2 text-sm leading-6 text-slate-500"
            ),
        ),
        rx.el.div(
            rx.el.button(
                rx.icon(
                    "refresh-cw",
                    class_name=rx.cond(
                        S.loading, "h-4 w-4 animate-spin", "h-4 w-4"
                    ),
                ),
                "Refresh",
                on_click=S.load,
                disabled=S.loading | S.busy,
                class_name="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm font-medium text-slate-600 hover:bg-slate-50 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
            ),
            action,
            class_name="flex shrink-0 items-center gap-2",
        ),
        class_name="mb-8 flex flex-wrap items-center justify-between gap-5",
    )


def input_field(
    label: str, name: str, field_type: str = "text", required: bool = False
) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=name,
            class_name="mb-2 block text-sm font-medium text-slate-700",
        ),
        rx.el.input(
            id=name,
            name=name,
            type=field_type,
            default_value=S.draft[name],
            key=S.draft[name],
            required=required,
            class_name="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 outline-hidden focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15",
        ),
    )


def text_field(label: str, name: str, hint: str = "") -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=name,
            class_name="mb-2 block text-sm font-medium text-slate-700",
        ),
        rx.el.textarea(
            id=name,
            name=name,
            default_value=S.draft[name],
            key=S.draft[name],
            rows=4,
            class_name="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 font-mono text-xs leading-5 text-slate-800 outline-hidden focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15",
        ),
        rx.el.p(hint, class_name="mt-1 text-xs leading-5 text-slate-500"),
    )


def select_field(label: str, name: str, options: list[str]) -> rx.Component:
    return rx.el.div(
        rx.el.label(
            label,
            html_for=name,
            class_name="mb-2 block text-sm font-medium text-slate-700",
        ),
        rx.el.div(
            rx.el.select(
                rx.foreach(
                    options, lambda item: rx.el.option(item, value=item)
                ),
                id=name,
                name=name,
                default_value=S.draft[name],
                key=S.draft[name],
                class_name="w-full appearance-none rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-800 focus-visible:ring-2 focus-visible:ring-teal-600",
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-3 h-4 w-4 text-slate-400",
            ),
            class_name="relative",
        ),
    )


def schema_help() -> rx.Component:
    return rx.el.details(
        rx.el.summary(
            "Rule parameter schema · v1",
            class_name="cursor-pointer text-sm font-semibold text-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600",
        ),
        rx.el.div(
            rx.el.p(
                'Selectors: {"keys":["primitive-key"]}, {"category":"Data"}, or {"properties":{"stateful":true}}. Fields combine with AND; keys are alternatives. Copy stable keys from the primitive library.',
                class_name="text-xs leading-6 text-slate-600",
            ),
            rx.el.pre(
                'pairwise: {"a": selector, "b": selector, "relation": "require" | "exclude"}\nconditional: {"when": selector, "require": selector}\nexclusive: {"members": [selector, selector], "max_count": 1}\nquantitative: {"metric": "cost" | "node_count" | "property", "property": "numeric_name", "scope": selector, "min": 0, "max": 100}\nemergent: {"all": [selector, selector], "effect": "Description", "outcome": "capability" | "conflict"}',
                class_name="mt-2 overflow-x-auto whitespace-pre-wrap rounded-lg bg-slate-100 p-3 text-[11px] leading-6 text-slate-700",
            ),
            rx.el.p(
                "scope, min and max are optional; at least one bound is required. property is used only for metric=property. Costs and numeric properties sum across matching nodes. Emergent outcome is optional: capability (default) or conflict. Conflict outcomes create findings using the rule severity.",
                class_name="mt-2 text-xs leading-5 text-slate-500",
            ),
            class_name="mt-3",
        ),
        class_name="rounded-lg border border-teal-100 bg-teal-50/50 p-4",
    )


def record_editor() -> rx.Component:
    return rx.cond(
        S.editor != "",
        rx.el.div(
            rx.el.section(
                rx.el.div(
                    rx.el.div(
                        rx.el.h2(
                            rx.cond(
                                S.edit_key == "", "Create record", "Edit record"
                            ),
                            class_name="text-xl font-semibold text-[#14253d]",
                        ),
                        rx.el.p(
                            rx.cond(
                                S.editor == "primitive",
                                "Define a reusable architecture building block.",
                                "Define a constraint for your architecture.",
                            ),
                            class_name="mt-1 text-sm text-slate-500",
                        ),
                    ),
                    rx.el.button(
                        rx.icon("x", class_name="h-5 w-5"),
                        aria_label="Close editor",
                        on_click=S.close_editor,
                        disabled=S.busy,
                        class_name="rounded-lg p-2 text-slate-500 hover:bg-slate-100 focus-visible:ring-2 focus-visible:ring-teal-600",
                    ),
                    class_name="flex items-start justify-between gap-4",
                ),
                rx.el.div(feedback(), class_name="mt-4"),
                rx.el.form(
                    input_field("Name *", "name", required=True),
                    rx.cond(
                        S.editor == "primitive",
                        rx.el.div(
                            rx.el.div(
                                input_field(
                                    "Category *", "category", required=True
                                ),
                                input_field(
                                    "Monthly cost estimate *",
                                    "cost",
                                    "number",
                                    True,
                                ),
                                class_name="grid gap-4 sm:grid-cols-2",
                            ),
                            text_field("Description", "description"),
                            text_field(
                                "Properties JSON",
                                "properties",
                                'An object of exact-match properties, e.g. {"stateful": true}.',
                            ),
                            text_field(
                                "Typed ports JSON",
                                "ports",
                                '[{"name":"in","direction":"input","type":"http","required":false}]. Names are unique; direction is input/output; type is a nonempty protocol string. Optional multiple is boolean.',
                            ),
                            text_field(
                                "Metadata JSON",
                                "metadata",
                                "An object for supplementary information; not used by rule matching.",
                            ),
                            class_name="flex flex-col gap-4",
                        ),
                        rx.el.div(
                            rx.el.div(
                                select_field(
                                    "Type",
                                    "type",
                                    [
                                        "pairwise",
                                        "conditional",
                                        "exclusive",
                                        "quantitative",
                                        "emergent",
                                    ],
                                ),
                                select_field(
                                    "Severity",
                                    "severity",
                                    ["error", "warning", "info"],
                                ),
                                select_field(
                                    "Enabled", "enabled", ["true", "false"]
                                ),
                                class_name="grid gap-4 sm:grid-cols-3",
                            ),
                            schema_help(),
                            text_field(
                                "Condition parameters JSON *",
                                "parameters",
                                "Parameters are checked on the backend before saving.",
                            ),
                            text_field("Explanation *", "explanation"),
                            text_field("Repair hint", "repair_hint"),
                            class_name="flex flex-col gap-4",
                        ),
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            type="button",
                            on_click=S.close_editor,
                            disabled=S.busy,
                            class_name="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-600 focus-visible:ring-2 focus-visible:ring-teal-600",
                        ),
                        rx.el.button(
                            rx.cond(S.busy, "Saving…", "Save record"),
                            type="submit",
                            disabled=S.busy | S.loading,
                            class_name="rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 focus-visible:ring-2 focus-visible:ring-teal-600 disabled:opacity-50",
                        ),
                        class_name="flex justify-end gap-3 border-t border-slate-200 pt-5",
                    ),
                    on_submit=S.submit,
                    key=S.revision,
                    class_name="mt-5 flex flex-col gap-5",
                ),
                role="dialog",
                aria_modal=True,
                aria_label="Record editor",
                class_name="max-h-[90dvh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-200 bg-white p-6",
            ),
            class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#14253d]/60 p-4",
        ),
    )


def confirmation_dialogs() -> rx.Component:
    return rx.fragment(
        rx.cond(
            S.delete_key != "",
            rx.el.div(
                rx.el.section(
                    rx.el.h2(
                        "Delete this record?",
                        class_name="text-xl font-semibold text-[#14253d]",
                    ),
                    rx.el.p(
                        S.delete_name,
                        class_name="mt-3 font-medium text-slate-700",
                    ),
                    rx.el.p(
                        "This cannot be undone. Primitives referenced by compositions or rules cannot be deleted.",
                        class_name="mt-2 text-sm leading-6 text-slate-500",
                    ),
                    feedback(),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            on_click=S.cancel_delete,
                            disabled=S.busy,
                            class_name="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 focus-visible:ring-2 focus-visible:ring-teal-600",
                        ),
                        rx.el.button(
                            rx.cond(S.busy, "Deleting…", "Delete record"),
                            on_click=S.confirm_delete,
                            disabled=S.busy | S.loading,
                            class_name="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white focus-visible:ring-2 focus-visible:ring-red-600 disabled:opacity-50",
                        ),
                        class_name="mt-5 flex justify-end gap-3",
                    ),
                    role="dialog",
                    aria_modal=True,
                    aria_label="Confirm deletion",
                    class_name="w-full max-w-md rounded-2xl bg-white p-6",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#14253d]/60 p-4",
            ),
        ),
        rx.cond(
            S.reset_confirmation,
            rx.el.div(
                rx.el.section(
                    rx.el.h2(
                        "Reset the demo workspace?",
                        class_name="text-xl font-semibold text-[#14253d]",
                    ),
                    rx.el.p(
                        "Replaces all demo primitives, rules, compositions and demo activity, including your edits to those records. Custom records are preserved. Custom references to demo keys remain intact.",
                        class_name="my-4 text-sm leading-6 text-slate-600",
                    ),
                    feedback(),
                    rx.el.div(
                        rx.el.button(
                            "Cancel",
                            on_click=S.cancel_reset,
                            disabled=S.busy,
                            class_name="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 focus-visible:ring-2 focus-visible:ring-teal-600",
                        ),
                        primary_button(
                            "Reset demo", "rotate-ccw", S.reset_demo
                        ),
                        class_name="flex justify-end gap-3",
                    ),
                    role="dialog",
                    aria_modal=True,
                    aria_label="Confirm demo reset",
                    class_name="w-full max-w-md rounded-2xl bg-white p-6",
                ),
                class_name="fixed inset-0 z-50 flex items-center justify-center bg-[#14253d]/60 p-4",
            ),
        ),
    )


def shell(active: str, content: rx.Component) -> rx.Component:
    return rx.el.div(
        mobile_navigation(active),
        rx.el.div(
            navigation(active),
            rx.el.main(
                rx.el.div(
                    content,
                    class_name="mx-auto w-full max-w-[1600px] p-5 sm:p-8 xl:p-10",
                ),
                class_name="min-w-0 w-full flex-1 overflow-y-auto bg-[#f7f9fb]",
            ),
            class_name="flex min-h-0 flex-1",
        ),
        record_editor(),
        confirmation_dialogs(),
        class_name="flex h-dvh w-full flex-col overflow-hidden bg-[#f7f9fb] font-['Inter'] text-slate-700",
    )

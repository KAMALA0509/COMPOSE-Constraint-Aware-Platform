import reflex as rx

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Activity, Composition, Primitive, Rule
from app.services.rule_schema import evaluate


def demo_primitives() -> list[dict]:
    specs = [
        (
            "edge-gateway",
            "API Gateway",
            "Compute",
            "Routes external requests and enforces API policies.",
            45,
            {"public": True},
            "http",
            "http",
        ),
        (
            "web-app",
            "Web Application",
            "Compute",
            "Serves interactive browser experiences.",
            35,
            {"public": True},
            "http",
            "http",
        ),
        (
            "app-service",
            "Application Service",
            "Compute",
            "Runs core business logic behind the gateway.",
            55,
            {"stateful": False},
            "http",
            "sql",
        ),
        (
            "worker",
            "Background Worker",
            "Compute",
            "Processes asynchronous jobs from a queue.",
            25,
            {"async": True},
            "event",
            "sql",
        ),
        (
            "scheduler",
            "Job Scheduler",
            "Compute",
            "Publishes recurring work on a schedule.",
            15,
            {"scheduled": True},
            "http",
            "event",
        ),
        (
            "function",
            "Serverless Function",
            "Compute",
            "Executes short-lived event handlers.",
            20,
            {"serverless": True},
            "event",
            "http",
        ),
        (
            "postgres",
            "PostgreSQL",
            "Data",
            "Relational system of record with ACID transactions.",
            80,
            {"database": True, "stateful": True, "relational": True},
            "sql",
            "sql",
        ),
        (
            "mysql",
            "MySQL",
            "Data",
            "Alternative relational database for transactional workloads.",
            70,
            {"database": True, "stateful": True, "relational": True},
            "sql",
            "sql",
        ),
        (
            "redis",
            "Redis Cache",
            "Data",
            "Low-latency cache for hot reads and sessions.",
            30,
            {"cache": True, "stateful": True},
            "cache",
            "cache",
        ),
        (
            "object-store",
            "Object Storage",
            "Data",
            "Durable storage for uploads and large binary objects.",
            20,
            {"durable": True, "stateful": True},
            "blob",
            "blob",
        ),
        (
            "search-index",
            "Search Index",
            "Data",
            "Indexes documents for full-text discovery.",
            50,
            {"search": True, "stateful": True},
            "document",
            "http",
        ),
        (
            "backup",
            "Backup Vault",
            "Data",
            "Retains encrypted recovery snapshots.",
            18,
            {"backup": True, "durable": True},
            "snapshot",
            "snapshot",
        ),
        (
            "load-balancer",
            "Load Balancer",
            "Connectivity",
            "Distributes incoming HTTP traffic across services.",
            25,
            {"ingress": True},
            "http",
            "http",
        ),
        (
            "cdn",
            "Content Delivery Network",
            "Connectivity",
            "Caches static content close to users.",
            22,
            {"public": True, "edge": True},
            "http",
            "http",
        ),
        (
            "queue",
            "Message Queue",
            "Connectivity",
            "Buffers jobs and supports independent consumers.",
            28,
            {"messaging": True},
            "event",
            "event",
        ),
        (
            "event-bus",
            "Event Bus",
            "Connectivity",
            "Fans domain events out to subscribers.",
            32,
            {"messaging": True, "fanout": True},
            "event",
            "event",
        ),
        (
            "service-mesh",
            "Service Mesh",
            "Connectivity",
            "Provides service-to-service identity and routing.",
            40,
            {"mesh": True},
            "http",
            "http",
        ),
        (
            "private-network",
            "Private Network",
            "Connectivity",
            "Isolates internal workloads from public ingress.",
            12,
            {"isolation": True},
            "network",
            "network",
        ),
        (
            "identity",
            "Identity Provider",
            "Operations",
            "Authenticates users and issues access tokens.",
            25,
            {"security": True},
            "http",
            "token",
        ),
        (
            "waf",
            "Web Application Firewall",
            "Operations",
            "Filters malicious public HTTP requests.",
            20,
            {"security": True, "perimeter": True},
            "http",
            "http",
        ),
        (
            "secrets",
            "Secrets Manager",
            "Operations",
            "Controls credential storage and rotation.",
            15,
            {"security": True, "secrets": True},
            "http",
            "secret",
        ),
        (
            "metrics",
            "Metrics Collector",
            "Operations",
            "Collects health and performance telemetry.",
            18,
            {"observability": True},
            "metric",
            "metric",
        ),
        (
            "logging",
            "Log Aggregator",
            "Operations",
            "Centralizes structured operational logs.",
            22,
            {"observability": True, "logs": True},
            "log",
            "log",
        ),
        (
            "tracing",
            "Distributed Tracing",
            "Operations",
            "Correlates requests across service boundaries.",
            20,
            {"observability": True, "traces": True},
            "trace",
            "trace",
        ),
    ]
    return [
        dict(
            key=f"demo:{key}",
            name=name,
            category=category,
            description=description,
            cost=float(cost),
            properties=properties,
            ports=[
                {
                    "name": "in",
                    "direction": "input",
                    "type": input_type,
                    "required": False,
                },
                {
                    "name": "out",
                    "direction": "output",
                    "type": output_type,
                    "multiple": True,
                },
            ],
            metadata={
                "demo": True,
                "domain": "System Architecture",
                "cost_unit": "monthly estimate",
            },
        )
        for key, name, category, description, cost, properties, input_type, output_type in specs
    ]


def demo_rules() -> list[dict]:
    def key(name: str) -> dict:
        return {"keys": [f"demo:{name}"]}

    specs = [
        (
            "gateway-identity",
            "Gateway requires identity",
            "pairwise",
            "error",
            {
                "a": key("edge-gateway"),
                "b": key("identity"),
                "relation": "require",
            },
            "API ingress must authenticate callers.",
            "Add an Identity Provider.",
        ),
        (
            "postgres-backup",
            "PostgreSQL requires backups",
            "pairwise",
            "error",
            {"a": key("postgres"), "b": key("backup"), "relation": "require"},
            "Transactional data needs a recovery path.",
            "Add a Backup Vault.",
        ),
        (
            "worker-queue",
            "Workers require a queue",
            "pairwise",
            "error",
            {"a": key("worker"), "b": key("queue"), "relation": "require"},
            "Background workers need a buffered job source.",
            "Add a Message Queue.",
        ),
        (
            "mysql-backup",
            "MySQL requires backups",
            "pairwise",
            "error",
            {"a": key("mysql"), "b": key("backup"), "relation": "require"},
            "MySQL data must be recoverable.",
            "Add a Backup Vault.",
        ),
        (
            "public-waf",
            "Protect public workloads",
            "conditional",
            "error",
            {"when": {"properties": {"public": True}}, "require": key("waf")},
            "Public endpoints require perimeter protection.",
            "Add a Web Application Firewall.",
        ),
        (
            "stateful-private",
            "Isolate stateful workloads",
            "conditional",
            "error",
            {
                "when": {"properties": {"stateful": True}},
                "require": key("private-network"),
            },
            "Stateful services should remain on a private network.",
            "Add a Private Network.",
        ),
        (
            "compute-metrics",
            "Observe compute workloads",
            "conditional",
            "warning",
            {"when": {"category": "Compute"}, "require": key("metrics")},
            "Compute health should be observable.",
            "Add a Metrics Collector.",
        ),
        (
            "database-secrets",
            "Manage database credentials",
            "conditional",
            "error",
            {
                "when": {"properties": {"database": True}},
                "require": key("secrets"),
            },
            "Database credentials require managed storage.",
            "Add a Secrets Manager.",
        ),
        (
            "one-relational",
            "Choose one relational database",
            "exclusive",
            "error",
            {"members": [key("postgres"), key("mysql")], "max_count": 1},
            "This reference architecture supports a single relational engine.",
            "Keep PostgreSQL or MySQL, not both.",
        ),
        (
            "one-messaging",
            "Keep messaging focused",
            "exclusive",
            "warning",
            {"members": [key("queue"), key("event-bus")], "max_count": 1},
            "Multiple messaging backbones increase operating complexity.",
            "Prefer a single backbone unless fanout is essential.",
        ),
        (
            "one-edge",
            "Choose one public front door",
            "exclusive",
            "warning",
            {
                "members": [key("edge-gateway"), key("load-balancer")],
                "max_count": 1,
            },
            "Two ingress layers may duplicate routing responsibilities.",
            "Consolidate ingress responsibilities.",
        ),
        (
            "budget",
            "Reference monthly budget",
            "quantitative",
            "error",
            {"metric": "cost", "max": 650},
            "Total monthly estimate must not exceed 650 cost units.",
            "Remove unnecessary components or reduce scope.",
        ),
        (
            "minimum",
            "Minimum useful system",
            "quantitative",
            "error",
            {"metric": "node_count", "min": 3},
            "A reference system needs at least three components.",
            "Add supporting infrastructure.",
        ),
        (
            "complexity",
            "Keep the system understandable",
            "quantitative",
            "warning",
            {"metric": "node_count", "max": 16},
            "More than sixteen components increases operational overhead.",
            "Consolidate responsibilities.",
        ),
        (
            "compute-cap",
            "Compute budget guardrail",
            "quantitative",
            "warning",
            {"metric": "cost", "scope": {"category": "Compute"}, "max": 180},
            "Compute spending should remain below 180 cost units.",
            "Reduce redundant compute services.",
        ),
        (
            "async-decoupling",
            "Asynchronous decoupling",
            "emergent",
            "info",
            {
                "all": [key("app-service"), key("queue"), key("worker")],
                "effect": "Business requests and background processing can scale independently.",
            },
            "A producer, queue and worker create decoupled processing.",
            "Keep queue boundaries explicit.",
        ),
        (
            "observability",
            "Full-stack observability",
            "emergent",
            "info",
            {
                "all": [key("metrics"), key("logging"), key("tracing")],
                "effect": "Metrics, logs and traces support correlated incident investigation.",
            },
            "Three telemetry signals create richer operational insight.",
            "Use shared correlation identifiers.",
        ),
        (
            "recovery",
            "Recoverable relational storage",
            "emergent",
            "info",
            {
                "all": [
                    {"properties": {"relational": True}},
                    key("backup"),
                    key("private-network"),
                ],
                "effect": "Private relational storage with backups supports a recoverable data tier.",
            },
            "Isolation and snapshots strengthen data resilience.",
            "Test restoration regularly.",
        ),
    ]
    specs.append(
        (
            "three-way-ingress",
            "Three-way ingress ambiguity",
            "emergent",
            "error",
            {
                "all": [
                    key("edge-gateway"),
                    key("load-balancer"),
                    key("service-mesh"),
                ],
                "outcome": "conflict",
                "effect": "Three independent routing authorities create ambiguous ingress ownership.",
            },
            "Gateway, load balancer and service mesh together create ambiguous ingress ownership.",
            "Remove one routing authority; all three are needed to trigger this conflict.",
        )
    )
    return [
        dict(
            key=f"demo:rule:{key_name}",
            name=name,
            type=kind,
            severity=severity,
            enabled=True,
            parameters=params,
            explanation=explanation,
            repair_hint=hint,
        )
        for key_name, name, kind, severity, params, explanation, hint in specs
    ]


def seed_demo(session: Session, replace: bool = False) -> None:
    if session.get_bind().dialect.name == "postgresql":
        session.execute(text("SELECT pg_advisory_xact_lock(731904228)"))
    if replace:
        for model in (Composition, Rule, Primitive):
            for record in session.scalars(
                select(model).where(model.key.like("demo:%"))
            ).all():
                session.delete(record)
        for record in session.scalars(
            select(Activity).where(Activity.entity_key.like("demo:%"))
        ).all():
            session.delete(record)
        session.flush()
    primitives, rules = demo_primitives(), demo_rules()
    existing_primitives = set(session.scalars(select(Primitive.key)).all())
    existing_rules = set(session.scalars(select(Rule.key)).all())
    existing_compositions = set(session.scalars(select(Composition.key)).all())
    for item in primitives:
        if item["key"] in existing_primitives:
            continue
        session.add(
            Primitive(
                key=item["key"],
                name=item["name"],
                category=item["category"],
                description=item["description"],
                cost=item["cost"],
                properties_json=item["properties"],
                ports_json=item["ports"],
                metadata_json=item["metadata"],
            )
        )
    for item in rules:
        if item["key"] in existing_rules:
            continue
        session.add(
            Rule(
                key=item["key"],
                name=item["name"],
                type=item["type"],
                severity=item["severity"],
                enabled=item["enabled"],
                parameters_json=item["parameters"],
                explanation=item["explanation"],
                repair_hint=item["repair_hint"],
            )
        )
    lookup = {item["key"]: item for item in primitives}
    examples = [
        (
            "valid",
            "Protected application stack",
            "A complete private application and data tier.",
            [
                "edge-gateway",
                "identity",
                "waf",
                "app-service",
                "postgres",
                "backup",
                "private-network",
                "secrets",
                "metrics",
            ],
        ),
        (
            "invalid",
            "Unprotected dual-database stack",
            "A deliberately risky example to inspect in the composer.",
            ["edge-gateway", "postgres", "mysql", "worker"],
        ),
        (
            "partial",
            "Application draft",
            "An incomplete starting point that still needs supporting services.",
            ["app-service"],
        ),
        (
            "emergent",
            "Decoupled observable system",
            "A complete asynchronous system with correlated telemetry.",
            ["app-service", "queue", "worker", "metrics", "logging", "tracing"],
        ),
    ]
    examples.append(
        (
            "three-way",
            "Three-way routing conflict",
            "All three routing authorities trigger the emergent conflict.",
            [
                "edge-gateway",
                "load-balancer",
                "service-mesh",
                "identity",
                "waf",
                "metrics",
            ],
        )
    )
    for slug, title, description, keys in examples:
        if f"demo:composition:{slug}" in existing_compositions:
            continue
        selected = [lookup[f"demo:{key}"] for key in keys]
        nodes = [
            {
                "id": f"n{index}",
                "primitive_key": item["key"],
                "position": {"x": (index % 4) * 240, "y": (index // 4) * 180},
            }
            for index, item in enumerate(selected)
        ]
        edges = []
        for index in range(len(selected) - 1):
            if (
                selected[index]["ports"][1]["type"]
                == selected[index + 1]["ports"][0]["type"]
            ):
                edges.append(
                    {
                        "id": f"e{index}",
                        "source": f"n{index}",
                        "source_port": "out",
                        "target": f"n{index + 1}",
                        "target_port": "in",
                    }
                )
        session.add(
            Composition(
                key=f"demo:composition:{slug}",
                title=title,
                description=description,
                nodes_json=nodes,
                edges_json=edges,
                validation_json=evaluate(selected, rules),
            )
        )
        session.add(
            Activity(
                action="Seeded",
                entity_type="composition",
                entity_key=f"demo:composition:{slug}",
                detail=title,
            )
        )
    if existing_compositions and not replace:
        return
    session.add(
        Activity(
            action="Demo reset" if replace else "Demo initialized",
            entity_type="workspace",
            entity_key="demo:workspace",
            detail="24 architecture primitives, 19 rules and 5 reference compositions.",
        )
    )

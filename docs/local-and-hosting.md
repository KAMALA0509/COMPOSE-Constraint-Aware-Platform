# Local operation and hosting guidance

Use Python 3.13, install the dependency manifest, and run `reflex run` from the repository root. Enterprise React Flow requires the enterprise package and any entitlement required by your Reflex installation. Configure environment values through your local shell or platform secrets, never committed source files. See the safe environment checklist.

The supplied managed workspace already provides PostgreSQL and handles migrations. Do not run database initialization or migration commands against it. For an independent environment, follow the current official Reflex database setup documentation with an administrator-provisioned database.

Startup and page loads safely initialize missing reference demo keys under a transaction lock. Reset intentionally replaces the reserved demo records, leaving custom records intact. Save writes a graph and evaluated snapshot transactionally. Failed writes retain the draft for retry.

No hosting service is configured or available through this implementation. No Vercel/Render deployment has been performed or promised. For future hosting use current official Reflex hosting guidance and a platform that supports the Reflex frontend, backend event connections and persistent PostgreSQL. Provision authentication, HTTPS, authorization, limits and backups before exposing a shared workspace. Validate enterprise component availability in the target environment. Do not publish secrets, connection strings or private platform settings in logs or documentation.

Validation and goal solving run on CPU and use bounded workloads. The solver limits runtime and search nodes; a large library may exhaust the budget rather than prove a result. Increase budgets within documented caps, narrow selectors or lower max_blocks when needed.

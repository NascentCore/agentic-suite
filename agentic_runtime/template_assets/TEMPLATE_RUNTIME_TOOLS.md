# TEMPLATE_RUNTIME_TOOLS.md

> Universal template for generating `RUNTIME_TOOLS.md` for a running application.
> Replace placeholders with actual runtime profile values.

# RUNTIME_TOOLS.md — {APP_NAME}

> Auto-generated tool catalogue for the running application.

## Application Info
- **Name**: {APP_NAME}
- **Type**: {APP_TYPE}
- **Base URL**: {BASE_URL}
- **Health endpoint**: {HEALTH_ENDPOINT}
- **Auth method**: {AUTH_METHOD}
- **Discovered capabilities**: {CAPABILITY_COUNT}

## Tool Catalogue

{CAPABILITY_LIST}

## Usage Notes
- Tools marked **high_impact** require explicit approval before execution.
- Tools marked **read_only** are safe for autonomous execution.
- All tool invocations are recorded with provenance metadata.

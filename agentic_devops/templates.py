"""Template system for generating DevOps agent configuration files.

Mirrors ``personified_software.openclaw_scaffold.templates`` and
``agentic_runtime.templates`` but produces *DevOps*-oriented documents:

- ``DEVOPS_RUNBOOK.md`` — deployment runbook
- ``DEPLOY_SKILLS.md`` — DevOps agent skill contract
- ``MONITOR_CONFIG.md`` — monitoring configuration reference
"""

from __future__ import annotations

from .models import DeployProfile


# ---------------------------------------------------------------------------
# DEVOPS_RUNBOOK.md
# ---------------------------------------------------------------------------

DEVOPS_RUNBOOK_TEMPLATE = """# DEVOPS_RUNBOOK.md — {APP_NAME}

> Auto-generated deployment and operations runbook.

## Application Info
- **Name**: {APP_NAME}
- **Repository**: {REPO_PATH}
- **Deploy method**: {DEPLOY_METHOD}
- **CI system**: {CI_SYSTEM}
- **Artifact type**: {ARTIFACT_TYPE}

## Environments

{ENVIRONMENT_LIST}

## Deployment Procedure

### Standard deployment
1. Code merged to main branch.
2. CI pipeline triggers automatically.
3. Build stage: compile / package / containerize.
4. Test stage: run automated test suite.
5. Deploy stage: push to target environment.
6. Verify stage: run health checks and smoke tests.

### Rollback procedure
1. Identify the last known-good version.
2. Execute rollback via pipeline or manual command.
3. Verify service health after rollback.
4. Create incident report if applicable.

## Monitoring
- Health checks run every 30 seconds.
- Consecutive failure threshold: 3 (before escalation).
- Alerts route to the on-call team.

## Incident Response
1. **Detect** — automated health checks or manual report.
2. **Diagnose** — analyze logs, metrics, recent deployments.
3. **Propose** — generate remediation options.
4. **Execute** — apply approved remediation action.
5. **Verify** — confirm service recovery.
6. **Reflect** — post-incident review and preventive action.

## Safety Rules
- Production deployments **always** require explicit approval.
- Rollbacks must be to a previously verified version.
- All deployment actions are logged with provenance.
"""


# ---------------------------------------------------------------------------
# DEPLOY_SKILLS.md
# ---------------------------------------------------------------------------

DEPLOY_SKILLS_TEMPLATE = """# DEPLOY_SKILLS.md — DevOps Agent Skill Contract

## Skill Name
`devops-deploy-monitor-skill`

## Goal
Provide a standard execution contract for agents to manage the CI/CD lifecycle
of **{APP_NAME}**: build, test, deploy, monitor, and incident response.

## Application Profile
- App name: **{APP_NAME}**
- Deploy method: **{DEPLOY_METHOD}**
- CI system: **{CI_SYSTEM}**
- Environments: {ENVIRONMENT_COUNT}

## Input Contract
Expect:
1. Deployment intent (deploy / rollback / scale / monitor).
2. Target environment.
3. Constraints (approval status, risk tolerance).

## Output Contract
Return:
1. Pipeline execution summary.
2. Health check results.
3. Incident diagnosis and remediation status.
4. Provenance record.

## Core Capabilities
### 1) Deploy
- Execute CI/CD pipeline stages in dependency order.
- Gate production deployments with approval.
- Record deployment version for rollback.

### 2) Monitor
- Run health check probes (HTTP, TCP, command).
- Evaluate aggregate system health.
- Auto-detect incidents from unhealthy status.

### 3) Incident Response
- Create incidents from health check failures.
- Generate diagnosis with hypotheses and evidence.
- Propose and execute remediation actions.
- Track incident lifecycle to resolution.

### 4) Rollback
- Track deployment version history per environment.
- Execute safe rollback to previous versions.
- Verify health after rollback.

## Standard Workflow
1. **Detect** — monitor health, detect anomalies.
2. **Diagnose** — analyze incident, generate hypotheses.
3. **Plan** — propose remediation with risk assessment.
4. **Gate** — evaluate policy, request approval if needed.
5. **Execute** — apply remediation or deployment.
6. **Verify** — confirm success via health checks.

## Hard Guardrails
- Never deploy to production without approval.
- Never skip health verification after deployment.
- Record all operations with provenance.
- Rollback depth limited by strategy configuration.
"""


# ---------------------------------------------------------------------------
# MONITOR_CONFIG.md
# ---------------------------------------------------------------------------

MONITOR_CONFIG_TEMPLATE = """# MONITOR_CONFIG.md — Monitoring Configuration Reference

## Application
- **Name**: {APP_NAME}
- **Environments**: {ENVIRONMENT_COUNT}

## Health Check Defaults
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Failure threshold**: 3 consecutive failures before escalation

## Check Types
### HTTP
- Target: URL endpoint
- Success: HTTP 2xx response within timeout

### TCP
- Target: host:port
- Success: TCP connection established within timeout

### Command
- Target: shell command
- Success: exit code 0 within timeout

### Metric Threshold
- Target: metric query expression
- Success: metric value within configured bounds

## Alert Routing
- **Warning** — notify team channel
- **Critical** — page on-call engineer + auto-create incident

## Incident Auto-Detection
- When a health check reaches the failure threshold, an incident is
  automatically created with severity based on check status.
- Duplicate detection prevents multiple incidents for the same check.

## Environments

{ENVIRONMENT_LIST}
"""


# ---------------------------------------------------------------------------
# Render functions
# ---------------------------------------------------------------------------

def render_devops_runbook(profile: DeployProfile) -> str:
    return DEVOPS_RUNBOOK_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"


def render_deploy_skills(profile: DeployProfile) -> str:
    return DEPLOY_SKILLS_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"


def render_monitor_config(profile: DeployProfile) -> str:
    return MONITOR_CONFIG_TEMPLATE.format(**profile.to_template_context()).strip() + "\n"

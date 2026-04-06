# TEMPLATE_DEVOPS_RUNBOOK.md

> Universal template for generating `DEVOPS_RUNBOOK.md`.
> Replace placeholders with actual deploy profile values.

# DEVOPS_RUNBOOK.md — {APP_NAME}

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

## Safety Rules
- Production deployments **always** require explicit approval.
- Rollbacks must be to a previously verified version.
- All deployment actions are logged with provenance.

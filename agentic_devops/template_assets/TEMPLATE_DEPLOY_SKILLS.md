# TEMPLATE_DEPLOY_SKILLS.md

> Universal template for generating `DEPLOY_SKILLS.md`.
> Replace placeholders with actual deploy profile values.

# DEPLOY_SKILLS.md — DevOps Agent Skill Contract

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

## Core Capabilities
- Deploy: execute CI/CD pipeline stages in dependency order
- Monitor: run health check probes
- Incident Response: detect, diagnose, propose, execute, verify
- Rollback: safe rollback to previous versions

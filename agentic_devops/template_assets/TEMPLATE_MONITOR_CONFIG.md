# TEMPLATE_MONITOR_CONFIG.md

> Universal template for generating `MONITOR_CONFIG.md`.
> Replace placeholders with actual deploy profile values.

# MONITOR_CONFIG.md — Monitoring Configuration Reference

## Application
- **Name**: {APP_NAME}
- **Environments**: {ENVIRONMENT_COUNT}

## Health Check Defaults
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Failure threshold**: 3 consecutive failures before escalation

## Check Types
- HTTP: URL endpoint, expects 2xx
- TCP: host:port, expects connection
- Command: shell command, expects exit code 0
- Metric Threshold: metric value within bounds

## Environments

{ENVIRONMENT_LIST}

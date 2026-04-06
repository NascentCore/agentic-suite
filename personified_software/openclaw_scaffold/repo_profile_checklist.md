# Repository Profile Checklist (Any Repo)

Use this checklist before generating `SOUL.md` / `skills.md` / `AGENTS.md` / `TOOLS.md` for a target repository.

## 1) Repository Identity
- [ ] Repository name and path
- [ ] Main purpose (library / service / tool / monorepo)
- [ ] Key stakeholders and expected users (if known)

## 2) Tech Stack
- [ ] Primary language
- [ ] Additional languages
- [ ] Dependency managers (`pip`, `npm`, `cargo`, etc.)
- [ ] Build tools and task runners

## 3) Structure
- [ ] Source directories
- [ ] Test directories
- [ ] Docs directories
- [ ] Entrypoints (`main.py`, service binaries, CLI entry scripts)

## 4) Validation Commands
- [ ] Install command
- [ ] Targeted test commands
- [ ] Run/demo commands
- [ ] Lint/typecheck commands (if applicable)

## 5) Governance & Risk
- [ ] Presence of secrets (`.env`, key files) and masking policy
- [ ] Deployment/infra directories requiring explicit approval
- [ ] CI workflow expectations
- [ ] High-impact operations that require confirmation

## 6) Agent Contract
- [ ] Boot sequence files and reading order
- [ ] Read/modify workflow requirements
- [ ] Hard guardrails (no fabrication, no destructive action without approval)

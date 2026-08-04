# workflows

Workflow schemas, step contracts, and step-owned agent charters for the
[orchestrator](https://github.com/ugudlado/orchestrator) engine.

Formerly published as `workflow-config`; the GitHub repo is now
[`ugudlado/workflows`](https://github.com/ugudlado/workflows).

## Layout

```text
config/
  workflows/           # feature.yaml, bugfix.yaml, …
  steps/<id>/
    contract.yaml      # prompt: SKILL.md  |  run: script.sh
    SKILL.md           # agent steps only (charter + scenarios live here)
    metrics.md
    scenarios/
    …
  lib/
  models.yaml
skills/                # compat symlinks → config/steps/* (optional for IDEs)
```

Agent prompts are **owned by the step**. Top-level `skills/` only mirrors them
for tooling that expects a `skills/` tree.

## Install into a consumer repo

```bash
uv tool install git+https://github.com/ugudlado/orchestrator.git
cd <your-repo>
orchestrator config pull https://github.com/ugudlado/workflows.git workflows
# or: orchestrator config pull /path/to/workflows workflows --skills
orchestrator doctor
orchestrator feature TICKET-1   # or orchestrator workflows/feature TICKET-1 if ambiguous
```

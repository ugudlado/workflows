# workflow-config

Workflow schemas, step contracts, and step-owned agent charters for the
[orchestrator](https://github.com/ugudlado/orchestrator) engine.

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
orchestrator config pull https://github.com/ugudlado/workflow-config.git mypack
# or: orchestrator config pull /path/to/workflow-config mypack --skills
orchestrator doctor
orchestrator feature TICKET-1   # or orchestrator mypack/feature TICKET-1 if ambiguous
```

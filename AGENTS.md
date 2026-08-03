# AGENTS.md

Guidance for agents editing **workflow-config** and for installing it into a
consumer repo via the orchestrator CLI.

---

## What this repo is

Pack source for [orchestrator](https://github.com/ugudlado/orchestrator):
workflow schemas, step contracts, and **step-owned** agent charters (`SKILL.md`
+ scenarios). Base role prompts (`extends:`) live separately in
[prompt-packs](https://github.com/ugudlado/prompt-packs).

---

## Source layout

```text
workflow-config/
  config/
    workflows/*.yaml          # feature, bugfix, complete, …
    steps/<id>/
      contract.yaml           # prompt: SKILL.md  |  run: script.sh
      SKILL.md                # agent steps only (canonical charter)
      metrics.md
      scenarios/
      …
    lib/
    models.yaml
  skills/<alias> → ../config/steps/<id>   # compat symlinks for IDEs
  AGENTS.md                   # this file (CLAUDE.md → symlink)
```

Charters live **in the step**. Do not reintroduce a separate skills tree as
source of truth. Top-level `skills/` only mirrors steps.

---

## Install into a consumer repo

```bash
uv tool install git+https://github.com/ugudlado/orchestrator.git
cd <consumer-repo>

orchestrator config pull https://github.com/ugudlado/workflow-config.git mypack
# local checkout:
orchestrator config pull /path/to/workflow-config mypack --skills

orchestrator doctor
orchestrator feature TICKET-1
# ambiguous across packs:
orchestrator mypack/feature TICKET-1
```

Consumer layout after pull:

```text
.orchestrator/mypack/workflows/feature.yaml
.orchestrator/mypack/steps/<id>/SKILL.md
```

`--skills` optionally creates `<repo>/skills/<name>` → step dirs for IDE tools.

---

## Editing rules

1. Agent steps: keep `prompt: SKILL.md` colocated with charter, metrics, scenarios.
2. Script steps: `run: script.sh` (or shared `lib/…`); no fake prompt.
3. Workflow YAML lists step ids only; contracts live under `steps/<id>/`.
4. Exclude GEPA `runs/` from commits (gitignored); don’t rely on them in contracts.
5. After structural changes, smoke:  
   `orchestrator config pull "$PWD" smoke-test --repo /tmp/…` and `doctor`.

More: root `README.md`, orchestrator `docs/distribution.md`.

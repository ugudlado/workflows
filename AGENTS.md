# AGENTS.md

Guidance for agents editing **workflows** and for installing it into a
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
workflows/
  config/
    workflows/*.yaml          # feature, bugfix, complete, …
    steps/<id>/
      contract.yaml           # prompt: SKILL.md  |  run: script.sh
      SKILL.md → prompt-packs  # charter symlink (see below)
      metrics.md
      scenarios/
      …
    lib/
    models.yaml
  skills/<alias> → ../config/steps/<id>   # compat symlinks for IDEs
  AGENTS.md                   # this file (CLAUDE.md → symlink)
```

Skill charters live in the sibling
[prompt-packs](https://github.com/ugudlado/prompt-packs) repo — the
machine-wide skills hub. Each role step's `SKILL.md` is a relative symlink
(`../../../../prompt-packs/roles/<alias>/SKILL.md`), so both repos must be cloned
as siblings (e.g. under `~/code/`). Edit charters in prompt-packs and
commit/push there; step machinery (contract.yaml, scenarios, scripts) stays
here. Alias map: architect=design, code-reviewer=code-review,
design-reviewer=design-review, developer=implement, ux-designer=ux-design,
ux-reviewer=ux-critique; explore+diagnose share roles/explore; learn keeps its name.
Install and update instructions for the skills themselves are in the
prompt-packs README — not duplicated here. Top-level `skills/` only
mirrors steps.

---

## Install into a consumer repo

```bash
uv tool install git+https://github.com/ugudlado/orchestrator.git
cd <consumer-repo>

orchestrator config pull https://github.com/ugudlado/workflows.git workflows
# local checkout:
orchestrator config pull /path/to/workflows workflows --skills

orchestrator doctor
orchestrator feature TICKET-1
# ambiguous across packs:
orchestrator workflows/feature TICKET-1
```

Consumer layout after pull:

```text
.orchestrator/workflows/workflows/feature.yaml
.orchestrator/workflows/steps/<id>/SKILL.md
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

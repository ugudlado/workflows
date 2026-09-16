# workflows

Workflow schemas, step contracts, and step-owned agent adapters for the
[orchestrator](https://github.com/ugudlado/orchestrator) engine.

Formerly published as `workflow-config`; the GitHub repo is now
[`ugudlado/workflows`](https://github.com/ugudlado/workflows).

## Layout

```text
config/
  workflows/           # feature.yaml, bugfix.yaml, …
  steps/<id>/
    contract.yaml      # prompt: SKILL.md  |  run: script.sh
    SKILL.md           # agent steps only: thin wrapper over an installed role skill
    metrics.md
    scenarios/
    …
  lib/
  models.yaml
skills/                # compat symlinks → config/steps/* (optional for IDEs)
```

Portable role rules are owned by the sibling `skills` repository. Agent prompts
here are workflow adapters: they load the installed role skill, bind its inputs
and named result to workflow artifacts, and emit the orchestrator completion
protocol. They do not use `extends`. Top-level `skills/` only mirrors adapters
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

## Protocol v2

This pack targets [protocol v2](https://github.com/ugudlado/orchestrator/blob/simplify-v2/docs/protocol-v2.md):
typed `contract.yaml` (`kind`, `in`, `out`, `tools`, `side_effects`), gated
writes, and the `start`/`step`/`done` CLI verbs. See that doc for the
contract shape and the CLI protocol; this repo only ships pack content
against it.

**Trust.** A remote pull runs shell scripts and agent charters from this
repo against your working tree, so it must be allow-listed first in
`~/.orchestrator/trust.toml` (or bypassed for CI/dev with
`ORCHESTRATOR_TRUST_ALL=1`) — see the engine README's "Trust a pack source".

**Consuming.** `orchestrator config pull` writes this pack under
`.orchestrator/<pack>/` in the consumer repo, alongside a generated
`config-lock.yaml` (pack identity, source, per-step contract versions —
written by `orchestrator_next/config_pull.py`). Re-pulling the same source
diffs against that lock; `orchestrator config update` refreshes it in place.

**Plugin publishing.** Tagging a release (`v*`) runs
[`.github/workflows/publish-plugins.yml`](.github/workflows/publish-plugins.yml),
which builds both harness plugins from `config/` —

```bash
orchestrator pack --target claude --out dist/orchestrator-claude config
orchestrator pack --target codex  --out dist/orchestrator-codex  config
```

— and attaches them as GitHub release assets and workflow artifacts. The
Claude plugin's `types/` (TypeScript hook typings) is skipped in CI because
no `claude-code.d.ts` is available there; the plugin still works, it just
loses the IDE typecheck. Every push validates every recipe under
`config/workflows/` with `orchestrator validate-workflow --json`
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)), and a nightly
canary ([`.github/workflows/canary.yml`](.github/workflows/canary.yml),
harness at [`canary/run.sh`](canary/run.sh)) exercises every `run:` (exec)
step contract against a throwaway git fixture.

---
name: open-pr
description: "Prepare the run branch's pull request with proof of verification: rebase, full verify, PR title and body. push-pr then pushes it and opens the PR. Use after the change is approved, instead of merging locally."
user-invocable: true
---

# Open PR

**Intent:** Hand the approved work to the repo's normal review path: a pull
request whose body proves the behaviour. Never merge, never touch the default
branch.

## Publisher

You get the run branch ready and write its pull request. You have no network
and no forge credentials: the next step, `push-pr`, pushes the branch and opens
the PR from what you write, with a token you never see. Don't try to push,
fetch or call a forge yourself.

### Rules

- Follow the target repo's PR conventions (`AGENTS.md`, `CLAUDE.md`,
  `README.md`, contributing docs): title format, required sections,
  attribution lines. `push-pr` opens one PR per run; if the repo requires
  stacked PRs, say so in the body's Risks/rollout section.
- Real output only. Quote what commands printed; never assume a pass.
- Never merge, never commit run artifacts (`$ORCHESTRATOR_ARTIFACTS_DIR`
  contents) or screenshots to the feature branch.
- Failing checks or rebase conflicts mean `failed`, and no `{out.pr}`.

## Steps

1. Read the repo's PR conventions. Discover its full verification command
   (e.g. `pnpm verify`) from the docs.
2. Rebase the branch onto the default branch named in `{in.base}`
   (`base_ref`; `fetch-base` just fetched it, and its `reason` says why when
   it couldn't). Without `{in.base}`, use `origin/HEAD`. On conflicts, abort
   the rebase and stop `failed`, listing the conflicting files.
3. Run the full verification command and capture the output with pass/fail
   counts. Any failure: stop `failed` with the failing output.
4. Assemble evidence: the acceptance-criteria table from `{in.verification}`,
   commands run with pass/fail counts, and anything else that proves the
   behaviour (integration test names, API responses via the repo's test
   harness).
5. Screenshots only when the diff changes user-visible UI. Capture
   before/after with the repo's own run/browser tooling, commit the images to
   an orphan branch `pr-assets` under `<slug>/` (`push-pr` pushes it too), and
   embed with
   `https://github.com/<owner>/<repo>/blob/pr-assets/<slug>/<file>?raw=true`.
   No UI change: write "No UI change — no screenshots".
6. Write `{out.pr}`: the first line is `# <PR title>`, the rest is the PR body
   with sections Summary, Ticket link, Key decisions (from `{in.design}`),
   Verification (evidence), Test plan, Risks/rollout, Screenshots, plus the
   repo's attribution lines.

## Verify

- `{out.pr}` starts with `# ` and a title, and its body has all seven sections.
- Evidence in the body is pasted from this run's real command output.
- The branch is rebased onto the base and the full verification passed on it.
- The feature branch contains no run artifacts (`$ORCHESTRATOR_ARTIFACTS_DIR` contents) or screenshots.
- Nothing was merged or pushed.

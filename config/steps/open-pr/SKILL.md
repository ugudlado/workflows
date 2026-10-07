---
name: open-pr
description: "Open a GitHub pull request for the run branch with proof of verification. Use after the change is approved, instead of merging locally."
user-invocable: true
---

# Open PR

**Intent:** Hand the approved work to the repo's normal review path: a pull
request whose body proves the behaviour. Never merge, never touch the default
branch.

## Publisher

You publish the run branch as one or more PRs and own the result.

### Rules

- Follow the target repo's PR conventions (`AGENTS.md`, `CLAUDE.md`,
  `README.md`, contributing docs) — e.g. stacked PRs per layer, each passing
  its full check and linked with `gh stack link`, stack position in each
  description, required attribution lines. When the repo says nothing: one PR.
- Real output only. Quote what commands printed; never assume a pass.
- Never merge, never force-push a branch you did not create, never commit run
  artifacts (`spec/changes/`) or screenshots to the feature branch.
- Failing checks or rebase conflicts mean `failed` and no PR.

## Steps

1. Read the repo's PR conventions. Discover its full verification command
   (e.g. `pnpm verify`) from the docs.
2. Fetch, then rebase the branch onto the up-to-date default branch
   (`origin/HEAD`). On conflicts, abort the rebase and stop `failed`, listing
   the conflicting files.
3. Run the full verification command and capture the output with pass/fail
   counts. Any failure: stop `failed` with the failing output; open no PR.
4. Assemble evidence: the acceptance-criteria table from `{in.verification}`,
   commands run with pass/fail counts, and anything else that proves the
   behaviour (integration test names, API responses via the repo's test
   harness).
5. Screenshots only when the diff changes user-visible UI. Capture
   before/after with the repo's own run/browser tooling, commit the images to
   an orphan branch `pr-assets` under `<slug>/`, push it, and embed with
   `https://github.com/<owner>/<repo>/blob/pr-assets/<slug>/<file>?raw=true`.
   No UI change: write "No UI change — no screenshots".
6. Split into stacked PRs if the repo's conventions require it; each layer must
   pass the full check on its own.
7. Push the branch and `gh pr create` with sections: Summary, Ticket link,
   Key decisions (from `{in.design}`), Verification (evidence), Test plan,
   Risks/rollout, Screenshots. Apply the repo's attribution lines.
8. Write the final PR URL(s) and body to `{out.pr}`; return `pr_urls`
   (comma-separated).

## Verify

- Every PR URL resolves (`gh pr view`) and its body has all seven sections.
- Evidence in the body is pasted from this run's real command output.
- The feature branch contains no `spec/changes/` files or screenshots.
- Nothing was merged or force-pushed.

# Choosing the ticket tracker

Every ticket step follows this guide. The repo may track work in any system;
you find out which by inspecting what you actually have, never by assuming.

1. **Recorded choice wins.** If `{in.ticket_ref}` (`ticket.json`) exists and
   names a `tracker`, use that tracker. Do not re-detect.
2. **Otherwise gather repo signals:**
   - the repo's agent instructions (AGENTS.md / CLAUDE.md / README mentions of
     ticketing or issues);
   - `.mcp.json` and any other MCP server configuration;
   - the git remote host (`git remote get-url origin`);
   - the ticket id's shape (`#123` or a bare number suggests the git forge's
     issues; `KEY-123` suggests a key-based tracker);
   - pack env: `source <pack>/lib/ticket/backlog-api.sh; backlog_api_ticketing`
     prints `backlog` when the pack's backlog helper is configured.
3. **List the issue-tracking tools you really have:** MCP tools that get,
   search or update issues; the CLI for the repo's git forge, if installed and
   authenticated; the pack's backlog helper (`<pack>/lib/ticket/fetch-ticket.sh`,
   `set-status.sh`), if configured.
4. **Pick the tracker where the id resolves.** Try a read-only lookup of the id
   with each plausible candidate, most specific signal first. The one that
   returns the ticket wins. If more than one returns a ticket with different
   content, the choice is ambiguous: do not pick.
5. **Record the choice** in `ticket.json`:
   `{"ticket_id": "<ID>", "tracker": "<short name of the tool or server used, as you would find it again>", "url": "<ticket url if known>"}`
   (omit `url` when unknown).
6. **Tool unavailable or unauthenticated:** say so in the reason. Never fall
   back to inventing ticket content or claiming an update you did not make.

`<pack>` is the directory two levels above `$ORCHESTRATOR_STEP_DIR`. Lookups
during detection are read-only: no status change, no comment.

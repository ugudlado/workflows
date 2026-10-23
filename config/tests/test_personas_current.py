"""
Regression — the Buzz personas must describe the engine and pack as they are now.

They drifted once (Redis state, `orchestrator run`/`done` long after both were
gone), so check what can be checked: the CLI verbs they use, the step ids
TeamLead routes, and no stale backends.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_CONFIG_DIR = Path(__file__).resolve().parent.parent
_PERSONAS = sorted((_CONFIG_DIR / "personas").glob("*.md"))
_STEPS = {p.name for p in (_CONFIG_DIR / "steps").iterdir() if p.is_dir()}

# The engine's only verb is `next`. Commands sit in code spans or code blocks.
_VERB = re.compile(r"(?:^|`|\$\()\s*orchestrator ([a-z][a-z-]*)", re.M)
_STALE = re.compile(r"redis|inngest|--seed-only|--schema|spec/changes/", re.I)


@pytest.mark.parametrize("path", _PERSONAS, ids=lambda p: p.name)
def test_persona_uses_only_current_cli(path: Path) -> None:
    text = path.read_text()
    assert {m.group(1) for m in _VERB.finditer(text)} <= {"next"}
    assert not _STALE.findall(text)


def test_teamlead_routes_only_real_steps() -> None:
    text = (_CONFIG_DIR / "personas" / "teamlead.md").read_text()
    table = text.split("## Persona mentions", 1)[1].split("##", 1)[0]
    routed = {
        sid.strip()
        for row in table.splitlines()
        if row.startswith("|") and "---" not in row and "step_id" not in row
        for sid in row.split("|")[1].split(",")
    }
    assert routed and routed <= _STEPS, routed - _STEPS

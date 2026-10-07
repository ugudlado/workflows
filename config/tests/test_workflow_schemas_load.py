"""Production schemas and contracts through the current stateless next API."""
from pathlib import Path

import pytest
import yaml

from orchestrator_next.nextstep import load_workflow, next_step, step_entries
from orchestrator_next.parser import AgentStepContract, ScriptStepContract, load_contract_for_step
from orchestrator_next.workflow_steps import step_id_of

_REAL_HOME = Path(__file__).resolve().parents[1]
_WORKFLOWS_DIR = _REAL_HOME / "workflows"
_USER_FACING_SCHEMAS = sorted(path.stem for path in _WORKFLOWS_DIR.glob("*.yaml"))


def _step_id_of(entry):
    return step_id_of(entry)


@pytest.mark.parametrize("schema_name", _USER_FACING_SCHEMAS)
def test_real_schema_loads_stateless_payloads(tmp_path, monkeypatch, schema_name):
    monkeypatch.chdir(tmp_path)
    schema = load_workflow(schema_name, _REAL_HOME)
    entries = step_entries(schema)
    expected_ids = [_step_id_of(entry) for entry in schema["steps"]]
    assert [entry["id"] for entry in entries] == expected_ids
    artifact_outputs = {}
    for entry in entries:
        if not entry["_gate"]:
            contract = load_contract_for_step(entry["id"], _REAL_HOME)
            artifact_outputs.update({
                name: f".orchestrator/runs/schema-load/artifacts/{spec['artifact']}"
                for name, spec in contract.outputs.items() if spec.get("artifact")
            })
    first = next_step(schema_name, config_root=_REAL_HOME, slug="schema-load")
    assert first["step_id"] == expected_ids[0] and first["route"] == "next"

    for index, entry in enumerate(entries):
        step_id = entry["id"]
        result = next_step(schema_name, config_root=_REAL_HOME, slug="schema-load",
                           after=step_id, status="abandoned")
        assert result["status"] == "ready"
        assert result["step_id"] == step_id and result["route"] == "retry"
        payload = result["payload"]
        if entry["_gate"]:
            assert result["kind"] == "gate"
            assert payload["approve_as"] == entry["approve_as"]
            # The stateless engine previews known outputs, not approval tokens.
            assert payload["show"] == {
                name: artifact_outputs[name] for name in entry["show"]
                if name in artifact_outputs
            }
            for path in payload["show"].values():
                assert not Path(path).is_absolute()
            continue

        contract_path = _REAL_HOME / "steps" / step_id / "contract.yaml"
        assert contract_path.is_file(), f"missing contract for {schema_name}/{step_id}"
        contract = load_contract_for_step(step_id, _REAL_HOME)
        assert payload["requires"] == entry.get("requires", "")
        assert payload["tools"] == contract.tools
        assert payload["side_effects"] == contract.side_effects
        for key, specs in (("in", contract.inputs), ("out", contract.outputs)):
            assert payload[key] == {
                name: f".orchestrator/runs/schema-load/artifacts/{spec['artifact']}"
                for name, spec in specs.items() if spec.get("artifact")
            }
        if isinstance(contract, ScriptStepContract):
            assert result["kind"] == "exec"
            assert Path(payload["run_path"]).is_file()
            advanced = next_step(schema_name, config_root=_REAL_HOME, slug="schema-load",
                                 after=step_id, status="completed")
            if index + 1 == len(entries):
                assert advanced["status"] == "done"
            else:
                assert advanced["step_id"] == expected_ids[index + 1]
                assert advanced["route"] == "next"
        else:
            assert isinstance(contract, AgentStepContract)
            assert result["kind"] == "judgment"
            assert Path(payload["prompt_path"]).is_file()

        if entry.get("on_failure"):
            failed = next_step(schema_name, config_root=_REAL_HOME, slug="schema-load",
                               after=step_id, status="failed")
            assert failed["step_id"] == entry["on_failure"]
            assert failed["route"] == "on_failure"
            exhausted = next_step(schema_name, config_root=_REAL_HOME, slug="schema-load",
                                  after=step_id, status="failed",
                                  attempt=entry.get("max_retries", 3))
            assert exhausted["status"] == "needs_you"
            assert exhausted["reason"] == "retries exhausted"

    assert list(tmp_path.iterdir()) == []  # No plan/state/run documents are written.


# ---------------------------------------------------------------------------
# Terminal steps — every current workflow ends at its report boundary.
# ---------------------------------------------------------------------------


def _schema_step_ids(schema_name):
    schema = yaml.safe_load((_WORKFLOWS_DIR / f"{schema_name}.yaml").read_text())
    return [
        _step_id_of(e)
        for e in (schema.get("steps") or [])
        if _step_id_of(e)
    ]


def _schema_step_entry(schema_name, step_id):
    schema = yaml.safe_load((_WORKFLOWS_DIR / f"{schema_name}.yaml").read_text())
    for entry in schema.get("steps") or []:
        if _step_id_of(entry) == step_id:
            return entry
    return None


_SCHEMA_TERMINAL_STEP = {
    "feature": "workflow-report",
    "bugfix": "workflow-report",
    "research": "workflow-report",
}


@pytest.mark.parametrize("schema_name,terminal_step", list(_SCHEMA_TERMINAL_STEP.items()))
def test_schema_ends_at_expected_terminal(schema_name, terminal_step):
    """Each production schema ends at its workflow boundary step."""
    steps = _schema_step_ids(schema_name)
    assert steps and steps[-1] == terminal_step, (
        f"{schema_name}.yaml steps must end with {terminal_step!r}, "
        f"got tail {steps[-3:]}"
    )


_SIGNOFF_GATES = {"merge-signoff", "pr-signoff"}


def _post_merge_workflows():
    found = []
    for name in _USER_FACING_SCHEMAS:
        steps = yaml.safe_load((_WORKFLOWS_DIR / f"{name}.yaml").read_text())["steps"]
        if any(isinstance(e, dict) and e.get("gate") in _SIGNOFF_GATES for e in steps):
            found.append(name)
    return found


def test_post_merge_workflow_set_is_expected():
    assert set(_post_merge_workflows()) == {"feature", "bugfix"}


@pytest.mark.parametrize("schema_name", _post_merge_workflows())
def test_post_merge_side_effect_steps_require_merge_token(schema_name):
    steps = yaml.safe_load((_WORKFLOWS_DIR / f"{schema_name}.yaml").read_text())["steps"]
    gate_idx = next(i for i, e in enumerate(steps)
                    if isinstance(e, dict) and e.get("gate") in _SIGNOFF_GATES)
    tokens = set()
    for entry in steps[gate_idx:]:
        if isinstance(entry, dict) and "gate" in entry:
            tokens.add(entry["approve_as"])
            continue
        step_id = step_id_of(entry)
        contract = load_contract_for_step(step_id, _REAL_HOME)
        if contract.side_effects:
            requires = entry.get("requires") if isinstance(entry, dict) else None
            assert requires in tokens, f"{schema_name}/{step_id} must require a token approved above it"


def test_intake_research_asks_then_advances(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ask = next_step("research", config_root=_REAL_HOME, slug="r1", after="intake-research",
                    status="completed",
                    out={"intake_status": "await_input", "ask": "Audience?"})
    assert ask["status"] == "needs_you"
    assert ask["step_id"] == "intake-research"
    assert ask["await_input"]["ask"] == "Audience?"

    intake = tmp_path / ".orchestrator" / "runs" / "r1" / "artifacts" / "intake.json"
    intake.parent.mkdir(parents=True)
    intake.write_text("{}")
    done = next_step("research", config_root=_REAL_HOME, slug="r1", after="intake-research",
                     status="completed", out={"intake_status": "complete"})
    assert done["step_id"] == "synthesize-findings"


def test_feature_schema_verifies_after_code_review():
    steps = _schema_step_ids("feature")
    assert steps.index("code-review") + 1 == steps.index("verify-changes")
    assert _schema_step_entry("feature", "verify-changes")["on_failure"] == "implement"


@pytest.mark.parametrize("schema_name", ["feature", "bugfix"])
def test_schema_ends_in_pr_not_merge(schema_name):
    steps = _schema_step_ids(schema_name)
    tail = steps[steps.index("mark-change-completed"):]
    assert tail == ["mark-change-completed", "open-pr", "pr-merged",
                    "remove-worktree", "ticket-done", "workflow-report"]
    assert not {"archive-completed-change", "merge-to-main"} & set(steps)
    assert _schema_step_entry(schema_name, "open-pr")["requires"] == "merge_token"
    for step in ("remove-worktree", "ticket-done"):
        assert _schema_step_entry(schema_name, step)["requires"] == "cleanup_token"


def test_open_pr_contract():
    contract = load_contract_for_step("open-pr", _REAL_HOME)
    assert isinstance(contract, AgentStepContract)
    assert contract.side_effects == ["write:remote"]
    assert contract.outputs["pr"]["artifact"] == "pr.md"
    assert contract.outputs["pr_urls"]["type"] == "string"

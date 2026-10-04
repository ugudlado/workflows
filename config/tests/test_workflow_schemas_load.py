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
                name: f"spec/changes/schema-load/{spec['artifact']}"
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
                name: f"spec/changes/schema-load/{spec['artifact']}"
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
    "patch": "workflow-report",
    "design": "workflow-report",
    "implement": "workflow-report",
    "feature-remote": "workflow-report",
    "research": "workflow-report",
    "complete": "workflow-report",
}


@pytest.mark.parametrize("schema_name,terminal_step", list(_SCHEMA_TERMINAL_STEP.items()))
def test_schema_ends_at_expected_terminal(schema_name, terminal_step):
    """Each production schema ends at its workflow boundary step."""
    steps = _schema_step_ids(schema_name)
    assert steps and steps[-1] == terminal_step, (
        f"{schema_name}.yaml steps must end with {terminal_step!r}, "
        f"got tail {steps[-3:]}"
    )


def test_complete_schema_includes_ticket_done():
    """Complete workflow syncs the ticket to Done before the terminal report."""
    steps = _schema_step_ids("complete")
    assert "ticket-done" in steps
    assert steps.index("archive-completed-change") < steps.index("ticket-done")


def test_complete_schema_merge_teardown_order():
    """complete.yaml: archive → merge-to-main → remove-worktree → ticket-done → workflow-report."""
    steps = _schema_step_ids("complete")
    order = ["archive-completed-change", "merge-to-main", "remove-worktree", "ticket-done", "workflow-report"]
    indices = [steps.index(s) for s in order]
    assert indices == sorted(indices), (
        f"complete.yaml steps out of order: {list(zip(order, indices))}"
    )


def test_patch_schema_retry_edges():
    """patch.yaml: implement and review carry ORC-120 retry routing.

    Default-edged fields are omitted from the workflow entry:
      - max_retries defaults to 3 in next_step
      - on_success defaults to advance (next declaration-order step)
    Only non-default routing survives in the schema.
    """
    implement = _schema_step_entry("patch", "implement")
    review = _schema_step_entry("patch", "code-review")
    assert isinstance(implement, dict)
    assert implement.get("on_failure") == "implement"
    assert "max_retries" not in implement  # engine default (3)
    assert isinstance(review, dict)
    assert "on_success" not in review  # advance to next step (ticket-qa)
    assert review.get("on_failure") == "implement"
    assert review.get("max_retries") == 8  # non-default, retained


def test_patch_schema_skips_the_design_phase_entirely():
    """patch.yaml goes ticket -> implement with no design phase at all.

    patch is the lightweight path. It previously kept a `design` step while
    skipping explore/diagnose, which left `design`'s `in.discovery` with no
    upstream producer — and the design charter fails hard on a missing
    discovery.md, so that step could never succeed. Protocol v2's wiring
    check surfaced it. implement/SKILL.md already documents the branch that
    derives work from ticket-context.md when design.md and tasks.yaml are
    both absent, which is the real patch path.
    """
    steps = _schema_step_ids("patch")
    design_phase_steps = {"explore", "diagnose", "design", "design-review", "ux-design"}
    assert design_phase_steps.isdisjoint(set(steps)), (
        f"patch.yaml must skip the design phase; found {design_phase_steps & set(steps)}"
    )
    assert "implement" in steps
    assert steps.index("create-worktree") < steps.index("implement")


def _post_merge_workflows():
    found = []
    for name in _USER_FACING_SCHEMAS:
        steps = yaml.safe_load((_WORKFLOWS_DIR / f"{name}.yaml").read_text())["steps"]
        if any(isinstance(e, dict) and e.get("gate") == "merge-signoff" for e in steps):
            found.append(name)
    return found


def test_post_merge_workflow_set_is_expected():
    assert set(_post_merge_workflows()) == {"feature", "feature-remote", "complete"}


@pytest.mark.parametrize("schema_name", _post_merge_workflows())
def test_post_merge_side_effect_steps_require_merge_token(schema_name):
    steps = yaml.safe_load((_WORKFLOWS_DIR / f"{schema_name}.yaml").read_text())["steps"]
    gate_idx = next(i for i, e in enumerate(steps)
                    if isinstance(e, dict) and e.get("gate") == "merge-signoff")
    for entry in steps[gate_idx + 1:]:
        step_id = step_id_of(entry)
        contract = load_contract_for_step(step_id, _REAL_HOME)
        if contract.side_effects:
            requires = entry.get("requires") if isinstance(entry, dict) else None
            assert requires == "merge_token", f"{schema_name}/{step_id}"


def test_intake_research_asks_then_advances(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ask = next_step("research", config_root=_REAL_HOME, slug="r1", after="intake-research",
                    status="completed",
                    out={"intake_status": "await_input", "ask": "Audience?"})
    assert ask["status"] == "needs_you"
    assert ask["step_id"] == "intake-research"
    assert ask["await_input"]["ask"] == "Audience?"

    intake = tmp_path / "spec" / "changes" / "r1" / "intake.json"
    intake.parent.mkdir(parents=True)
    intake.write_text("{}")
    done = next_step("research", config_root=_REAL_HOME, slug="r1", after="intake-research",
                     status="completed", out={"intake_status": "complete"})
    assert done["step_id"] == "synthesize-findings"

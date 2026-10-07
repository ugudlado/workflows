"""Deterministic scenario-learning gates; no models or real-pack commits."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest
import yaml

CONFIG = Path(__file__).resolve().parents[1]
STEPS = CONFIG / "steps"
spec = importlib.util.spec_from_file_location(
    "persist_learnings", STEPS / "persist-learnings" / "persist_learnings.py"
)
assert spec is not None and spec.loader is not None
persist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(persist)


def row(id="fresh", scenario="An export job loses its cancellation signal."):
    return {"id": id, "scenario": scenario, "expect": [
        "Locates the cancellation path", "Checks a cancelled job", "Records the observed result"
    ]}


def provenance():
    return {
        "source_kind": "agentmemory", "lesson_id": "lesson-7",
        "observed_outcome": "Cancelled export left a worker running",
        "verification": {"reference": "results/cancel-check.txt", "result": "passed"},
        "applicability": "The export worker still uses this cancellation path",
        "split_origin": "agentmemory",
    }


def accept(tmp_path, proposals, reserved=None):
    pack = tmp_path / "pack" / "steps" / "implement"
    (pack / "scenarios").mkdir(parents=True, exist_ok=True)
    if reserved:
        (pack / "scenarios" / "holdout.jsonl").write_text(json.dumps(reserved) + "\n")
    source = tmp_path / "proposals.jsonl"
    source.write_text("".join(json.dumps(p) + "\n" for p in proposals))
    accepted, skipped = persist._accept_rows([source], {"implement": str(pack)}, [tmp_path / "pack"])
    return pack, accepted, skipped


@pytest.mark.parametrize("step,keys", [
    ("human-review", ["decision_quality", "rework_routing"]),
    ("intake-research", ["intake_completeness", "resume_integrity"]),
    ("synthesize-findings", ["source_integrity", "audience_fit"]),
    ("verify-changes", ["criterion_coverage", "verification_evidence"]),
])
def test_initial_banks(step, keys):
    metrics = (STEPS / step / "metrics.md").read_text()
    assert "Metric keys: " + ", ".join(f"`{key}`" for key in keys) in metrics
    ids = set()
    situations = set()
    for split, count in [("train", 3), ("dev", 2), ("holdout", 2)]:
        rows = [persist.parse_line(line) for line in (STEPS / step / "scenarios" / f"{split}.jsonl").read_text().splitlines()]
        assert len(rows) == count
        for item in rows:
            persist.validate_scenario(item)
            assert 3 <= len(item["expect"]) <= 4
            assert item["id"] not in ids
            assert item["scenario"] not in situations
            ids.add(item["id"])
            situations.add(item["scenario"])


@pytest.mark.parametrize("shape", ["row", "scenario", "flat"])
def test_legacy_and_verified_proposals(tmp_path, shape):
    proposal: dict = {"step_id": "implement"}
    if shape == "flat":
        proposal.update(row())
    else:
        proposal[shape] = row()
    if shape == "row":
        proposal["provenance"] = provenance()
    pack, accepted, skipped = accept(tmp_path, [proposal])
    assert accepted == {pack: [row()]}
    assert skipped == []


@pytest.mark.parametrize("mutation", [
    {"verification": {"reference": "check.txt", "result": "failed"}},
    {"verification": {"reference": "check.txt", "result": "unverified"}},
    {"verification": {"reference": "", "result": "passed"}},
    {"verification": None}, {"observed_outcome": ""}, {"lesson_id": ""},
    {"applicability": ""}, {"split_origin": "holdout"}, {"split_origin": "dev"},
    {"source_kind": "confidence"},
])
def test_rejects_unverified_provenance(tmp_path, mutation):
    proof = {**provenance(), **mutation}
    _, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": row(), "provenance": proof}])
    assert not accepted
    assert len(skipped) == 1 and "provenance" in skipped[0]["reason"]


def test_confidence_only_is_not_evidence(tmp_path):
    _, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": row(), "provenance": {"confidence": 1.0}}])
    assert not accepted and skipped


def test_fresh_expectations_and_canonical_metadata(tmp_path):
    proposals = [
        {"step_id": "implement", "row": {**row("short"), "expect": ["One"]}},
        {"step_id": "implement", "row": {**row("long"), "expect": ["One"] * 5}},
        {"step_id": "implement", **row("flat"), "provenance": provenance()},
        {"step_id": "implement", "row": {**row("nested"), "provenance": provenance()}},
    ]
    _, accepted, skipped = accept(tmp_path, proposals)
    assert not accepted and len(skipped) == 4


def test_reserved_situation_cannot_be_reidentified(tmp_path):
    original = row("reserved", "A queue stalls after reconnect.")
    copied = row("other", "  a QUEUE  stalls after reconnect.  ")
    copied["expect"] = ["Different assertion", "Another assertion", "Last assertion"]
    _, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": copied}], original)
    assert not accepted and "duplicate scenario content" in skipped[0]["reason"]


def test_batch_and_existing_train_duplicates(tmp_path):
    proposal = {"step_id": "implement", "row": row()}
    pack, accepted, skipped = accept(tmp_path, [proposal, {"step_id": "implement", "row": row("renamed")}])
    assert accepted == {pack: [row()]} and len(skipped) == 1
    (pack / "scenarios" / "train.jsonl").write_text(json.dumps(row()) + "\n")
    _, accepted, skipped = accept(tmp_path, [proposal])
    assert not accepted and "duplicate scenario id" in skipped[0]["reason"]


def test_target_confinement_and_dirty_skip(tmp_path, monkeypatch):
    pack, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": row()}])
    source = tmp_path / "proposals.jsonl"
    rejected, reasons = persist._accept_rows([source], {"implement": str(pack)}, [tmp_path / "elsewhere"])
    assert not rejected and "outside" in reasons[0]["reason"]
    monkeypatch.setattr(persist, "git_root", lambda _: tmp_path)
    monkeypatch.setattr(persist, "is_dirty", lambda *_: True)
    persisted, repos = persist._persist(accepted, skipped, [tmp_path / "pack"])
    assert persisted == [] and repos == {}
    assert "uncommitted changes" in skipped[0]["reason"]
    assert not (pack / "scenarios" / "train.jsonl").exists()


def test_explicit_input_is_authoritative(tmp_path, monkeypatch):
    state = tmp_path / "legacy" / "state.yaml"
    state.parent.mkdir()
    legacy = state.parent / persist.STAGING_NAME
    legacy.write_text("legacy\n")
    explicit = tmp_path / "new.jsonl"
    explicit.write_text("explicit\n")
    monkeypatch.setenv("STATE_YAML_PATH", str(state))
    assert persist.staging_files(explicit) == [explicit]
    assert persist.staging_files(tmp_path / "absent.jsonl") == []
    assert persist.staging_files() == [legacy]


def test_real_next_payload_to_script_and_rerun(tmp_path, monkeypatch):
    from orchestrator_next.nextstep import next_step

    # Fence Git discovery: a fixture under a checkout is not inherently non-git.
    (tmp_path / ".git").write_text("invalid fixture Git fence\n")
    assert persist.git_root(tmp_path) is None
    pack = tmp_path / "pack"
    import shutil
    for step in ("learn", "persist-learnings", "implement"):
        shutil.copytree(STEPS / step, pack / "steps" / step, ignore=shutil.ignore_patterns("__pycache__"))
    (pack / "workflows").mkdir()
    (pack / "workflows" / "fixture.yaml").write_text(yaml.safe_dump({
        "artifacts_root": "artifacts/{slug}", "steps": ["implement", "learn", "persist-learnings"]
    }))
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    monkeypatch.chdir(worktree)
    payload = next_step("fixture", config_root=pack, slug="trial", after="learn", status="completed")["payload"]
    source = worktree / payload["in"]["proposed_scenarios"]
    assert source == worktree / "artifacts/trial/proposed-scenarios.jsonl"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps({"step_id": "implement", "row": row(), "provenance": provenance()}) + "\n")
    env = {**os.environ, **payload["env"]}
    for key in ("ORCHESTRATOR_PACK", "ORCHESTRATOR_PERSISTED_STEPS", "STATE_YAML_PATH", "ORCHESTRATOR_STATE_YAML_PATH", "ORCHESTRATOR_WORKFLOW_DIR"):
        env.pop(key, None)
    command = [payload["run_path"], "--proposed-scenarios", payload["in"]["proposed_scenarios"]]
    result = subprocess.run(command, cwd=worktree, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout.splitlines()[-1])
    assert output["outputs"]["persist_learnings"]["persisted"][0]["ids"] == ["fresh"]
    target = pack / "steps/implement/scenarios/train.jsonl"
    first = target.read_bytes()
    assert json.loads(first.splitlines()[-1]) == row()
    assert not source.exists()
    again = subprocess.run(command, cwd=worktree, env=env, capture_output=True, text=True)
    assert again.returncode == 0
    assert json.loads(again.stdout)["outputs"]["persist_learnings"]["persisted"] == []
    assert target.read_bytes() == first


def test_real_next_contract_payloads(monkeypatch, tmp_path):
    from orchestrator_next.nextstep import next_step, step_entries

    monkeypatch.chdir(tmp_path)
    for workflow in sorted((CONFIG / "workflows").glob("*.yaml")):
        doc = yaml.safe_load(workflow.read_text())
        for entry in step_entries(doc):
            result = next_step(workflow.stem, config_root=CONFIG, slug="contract-smoke",
                               after=entry["id"], status="abandoned")
            assert result["status"] == "ready"
            assert result["step_id"] == entry["id"]
            payload = result["payload"]
            if result["kind"] == "gate":
                continue
            path = payload["run_path"] if result["kind"] == "exec" else payload["prompt_path"]
            assert Path(path).is_file()
            for value in [*payload["in"].values(), *payload["out"].values()]:
                assert not Path(value).is_absolute()
            if entry["id"] == "persist-learnings":
                assert payload["in"]["proposed_scenarios"].endswith("/proposed-scenarios.jsonl")
                assert json.loads(payload["env"]["ORCHESTRATOR_PROMPT_DIRS"])


@pytest.mark.parametrize("raw", [
    '{"step_id":"implement","row":{"id":"a","id":"b","scenario":"Task","expect":["a","b","c"]}}',
    '{\n  "step_id": "implement"\n}',
    '[]',
])
def test_malformed_proposal_parsing(raw):
    with pytest.raises(persist.RowError):
        persist.parse_line(raw.splitlines()[0])


def test_run_history_provenance_without_memory_id(tmp_path):
    proof = provenance()
    proof.update(source_kind="run_history", split_origin="run_history")
    proof.pop("lesson_id")
    pack, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": row(), "provenance": proof}])
    assert accepted == {pack: [row()]} and skipped == []


def test_learning_training_oracle_matches_contract_output(tmp_path, monkeypatch):
    from orchestrator_next.nextstep import next_step

    contract = yaml.safe_load((STEPS / "learn" / "contract.yaml").read_text())
    output = "proposed_scenarios"
    monkeypatch.chdir(tmp_path)
    payload = next_step("feature", config_root=CONFIG, slug="oracle-check",
                        after="learn", status="abandoned")["payload"]
    assert Path(payload["out"][output]).name == contract["out"][output]["artifact"]
    cases = [json.loads(line) for line in (STEPS / "learn" / "scenarios" / "train.jsonl").read_text().splitlines()]
    case = next(item for item in cases if item["id"] == "learning-to-scenario-conversion")
    assert len(case["expect"]) == 5  # This original row is not a new proposal.
    assert case["expect"][0] == (
        "Converts the learning into an eval scenario proposed as one JSON line "
        f"at the contract-resolved {{out.{output}}} path"
    )


@pytest.mark.parametrize("oracle", ["metrics", "build-fails-after-done-claim"])
def test_verification_oracles_match_contract_output(oracle, tmp_path, monkeypatch):
    from orchestrator_next.nextstep import next_step

    contract = yaml.safe_load((STEPS / "verify-changes" / "contract.yaml").read_text())
    artifact = contract["out"]["verification"]["artifact"]
    monkeypatch.chdir(tmp_path)
    payload = next_step("feature", config_root=CONFIG, slug="oracle-check",
                        after="verify-changes", status="abandoned")["payload"]
    assert Path(payload["out"]["verification"]).name == artifact
    if oracle == "metrics":
        text = (STEPS / "verify-changes" / "metrics.md").read_text()
    else:
        cases = [json.loads(line) for line in (STEPS / "verify-changes" / "scenarios" / "dev.jsonl").read_text().splitlines()]
        case = next(item for item in cases if item["id"] == oracle)
        text = case["expect"][3]
    assert f"{{out.verification}} artifact (currently {artifact})" in text.replace("`", "")
    assert "verification.md" not in text


def test_learning_adapter_memory_safety_and_artifact_binding():
    text = (STEPS / "learn" / "SKILL.md").read_text()
    assert "agentmemory" in text and "untrusted data" in text
    assert "confidence alone" in text.lower()
    assert "current" in text and "verification" in text
    assert "Do not read dev/holdout" in text
    assert "{out.proposed_scenarios}" in text
    driver = (CONFIG / "DRIVER.md").read_text()
    assert "payload.in.proposed_scenarios" in driver and "--proposed-scenarios" in driver


def test_escaping_pack_link_is_not_confined(tmp_path):
    allowed = tmp_path / "allowed"
    allowed.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = allowed / "implement"
    link.symlink_to(outside, target_is_directory=True)
    assert not persist.is_confined(link, [allowed])
    source = tmp_path / "proposals.jsonl"
    source.write_text(json.dumps({"step_id": "implement", "row": row()}) + "\n")
    accepted, skipped = persist._accept_rows([source], {"implement": str(link)}, [allowed])
    assert accepted == {}
    assert len(skipped) == 1 and "outside" in skipped[0]["reason"]


@pytest.mark.parametrize("link_kind", ["scenarios", "existing", "dangling", "dev", "holdout"])
def test_append_rejects_redirected_training_target(tmp_path, monkeypatch, capsys, link_kind):
    (tmp_path / ".git").write_text("invalid fixture Git fence\n")
    assert persist.git_root(tmp_path) is None
    pack = tmp_path / "allowed" / "implement"
    pack.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    scenarios = pack / "scenarios"
    if link_kind == "scenarios":
        scenarios.symlink_to(outside, target_is_directory=True)
        redirected = outside / "train.jsonl"
    else:
        scenarios.mkdir()
        redirected = (scenarios / f"{link_kind}.jsonl" if link_kind in ("dev", "holdout")
                      else outside / "train.jsonl")
        (scenarios / "train.jsonl").symlink_to(redirected)
    if link_kind != "dangling":
        redirected.write_bytes(b"")
    before = redirected.read_bytes() if redirected.exists() else None
    source = tmp_path / "proposals.jsonl"
    source.write_text(json.dumps({"step_id": "implement", "row": row()}) + "\n")
    monkeypatch.setenv("ORCHESTRATOR_PROMPT_DIRS", json.dumps({"implement": str(pack)}))
    monkeypatch.setenv("ORCHESTRATOR_PROMPT_PATH", str(tmp_path / "allowed"))
    assert persist.run(source) == 0
    result = json.loads(capsys.readouterr().out)["outputs"]["persist_learnings"]
    assert result["persisted"] == []
    assert result["commits"] == []
    assert len(result["skipped"]) == 1
    assert "append target" in result["skipped"][0]["reason"]
    assert (redirected.read_bytes() if redirected.exists() else None) == before
    assert not source.exists()


@pytest.mark.parametrize("alias", [False, True])
def test_append_allows_normal_creation_and_trusted_root_alias(tmp_path, monkeypatch, capsys, alias):
    (tmp_path / ".git").write_text("invalid fixture Git fence\n")
    assert persist.git_root(tmp_path) is None
    root = tmp_path / "allowed"
    pack = root / "implement"
    pack.mkdir(parents=True)
    allowed = root
    if alias:
        allowed = tmp_path / "alias"
        allowed.symlink_to(root, target_is_directory=True)
        assert persist.is_confined(pack, [allowed])
        assert persist.is_confined(allowed / "implement", [root])
        pack = allowed / "implement"
    monkeypatch.setenv("ORCHESTRATOR_PROMPT_DIRS", json.dumps({"implement": str(pack)}))
    monkeypatch.setenv("ORCHESTRATOR_PROMPT_PATH", str(allowed))
    source = tmp_path / "proposals.jsonl"
    source.write_text(json.dumps({"step_id": "implement", "row": row()}) + "\n")
    assert persist.run(source) == 0
    result = json.loads(capsys.readouterr().out)["outputs"]["persist_learnings"]
    assert result["skipped"] == []
    assert result["persisted"][0]["ids"] == ["fresh"]
    assert result["commits"][0]["git_root"] is None
    assert json.loads((pack / "scenarios/train.jsonl").read_text()) == row()


@pytest.mark.parametrize("failure", [OSError, RuntimeError])
def test_confinement_resolution_failure_is_closed(tmp_path, monkeypatch, failure):
    def cannot_resolve(self, *args, **kwargs):
        raise failure("unresolvable path")
    monkeypatch.setattr(Path, "resolve", cannot_resolve)
    assert not persist.is_confined(tmp_path / "pack", [tmp_path])


def test_persist_rechecks_target_after_acceptance(tmp_path):
    (tmp_path / ".git").write_text("invalid fixture Git fence\n")
    assert persist.git_root(tmp_path) is None
    pack, accepted, skipped = accept(tmp_path, [{"step_id": "implement", "row": row()}])
    outside = tmp_path / "outside"
    outside.mkdir()
    (pack / "scenarios").rmdir()
    (pack / "scenarios").symlink_to(outside, target_is_directory=True)
    persisted, repos = persist._persist(accepted, skipped, [tmp_path / "pack"])
    assert persisted == [] and repos == {}
    assert len(skipped) == 1 and "unsafe append target" in skipped[0]["reason"]
    assert list(outside.iterdir()) == []


def test_confinement_does_not_suppress_resolution_errors(tmp_path, monkeypatch):
    def denied(self, strict=False):
        # Non-strict realpath suppresses some OS errors; a literal fallback
        # must not make an inaccessible child appear safely resolved.
        if strict:
            raise PermissionError("cannot inspect path")
        return self
    monkeypatch.setattr(Path, "resolve", denied)
    assert not persist.is_confined(tmp_path / "pack", [tmp_path])

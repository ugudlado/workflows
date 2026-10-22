"""collect-runs and mark-learned: the nightly learn workflow's exec steps."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

STEPS = Path(__file__).resolve().parents[1] / "steps"


def _load(step: str, module: str):
    spec = importlib.util.spec_from_file_location(module, STEPS / step / f"{module}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


collect = _load("collect-runs", "collect_runs")
mark = _load("mark-learned", "mark_learned")

FINISHED = [{"step": "workflow-report", "attempt": 1, "status": "completed"}]


def _run(root: Path, slug: str, history=FINISHED, **extra) -> Path:
    run_dir = root / slug
    run_dir.mkdir(parents=True)
    (run_dir / "state.yaml").write_text(yaml.safe_dump({"slug": slug, "step_history": history, **extra}))
    return run_dir


def _main(monkeypatch, capsys, out: Path, **env) -> dict:
    for key in ("ORCHESTRATOR_RUNS_DIR", "STATE_YAML_PATH", "ORCHESTRATOR_CHANGE_ID", "CHANGE_ID"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    monkeypatch.setattr("sys.argv", ["collect_runs.py", "--runs-out", str(out)])
    assert collect.main() == 0
    return json.loads(capsys.readouterr().out.splitlines()[-1])


def test_collects_only_finished_unlearned_other_runs(tmp_path, monkeypatch, capsys):
    root = tmp_path / "runs"
    done = _run(root, "orc-1")
    _run(root, "orc-2", history=[{"step": "open-pr", "status": "completed"}])  # unfinished
    _run(root, "orc-3", history=[{"step": "workflow-report", "status": "failed"}])
    learned = _run(root, "orc-4")
    (learned / "learned.json").write_text("{}")
    _run(root, "learn-1", workflow="learn")  # a learn run by recorded workflow name
    me = _run(root, "learn-2")  # the current learn run (finished-looking, unmarked)
    (root / "stray").mkdir()  # no state.yaml
    out = tmp_path / "artifacts" / "runs.json"
    result = _main(monkeypatch, capsys, out, STATE_YAML_PATH=me / "state.yaml")
    runs = json.loads(out.read_text())
    assert [r["slug"] for r in runs] == ["orc-1"]
    assert runs[0] == {
        "slug": "orc-1", "run_dir": str(done), "state_path": str(done / "state.yaml"),
        "artifacts_dir": str(done / "artifacts"), "finished_at": None,
    }
    assert result["outputs"] == {"runs": str(out), "run_count": 1}


def test_runs_dir_env_wins_and_zero_runs_is_success(tmp_path, monkeypatch, capsys):
    other = tmp_path / "elsewhere"
    other.mkdir()
    state = _run(tmp_path / "runs", "learn-2") / "state.yaml"
    out = tmp_path / "runs.json"
    result = _main(monkeypatch, capsys, out, ORCHESTRATOR_RUNS_DIR=other, STATE_YAML_PATH=state)
    assert json.loads(out.read_text()) == []
    assert result["outputs"]["run_count"] == 0 and result["status"] == "completed"


def test_missing_runs_root_is_empty_not_error(tmp_path, monkeypatch, capsys):
    out = tmp_path / "runs.json"
    result = _main(monkeypatch, capsys, out, ORCHESTRATOR_RUNS_DIR=tmp_path / "nope")
    assert result["outputs"]["run_count"] == 0


def test_mark_learned_writes_markers_idempotently(tmp_path, monkeypatch, capsys):
    root = tmp_path / "runs"
    a, b = _run(root, "orc-1"), _run(root, "orc-2")
    runs = tmp_path / "runs.json"
    runs.write_text(json.dumps([{"run_dir": str(a)}, {"run_dir": str(b)}, {"run_dir": str(root / "gone")}]))
    monkeypatch.setenv("ORCHESTRATOR_CHANGE_ID", "learn-9")
    monkeypatch.setattr("sys.argv", ["mark_learned.py", "--runs", str(runs), "--scenarios-appended", "2"])
    assert mark.main() == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["outputs"] == {"marked": 2}
    first = (a / "learned.json").read_text()
    record = json.loads(first)
    assert record["learn_run"] == "learn-9" and record["scenarios_appended"] == 2 and record["learned_at"]
    assert mark.main() == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["outputs"] == {"marked": 0}
    assert (a / "learned.json").read_text() == first
    # Marked runs drop out of the next collection.
    assert collect.collect(root) == []


def test_mark_learned_without_runs_is_noop(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["mark_learned.py", "--runs", str(tmp_path / "absent.json")])
    assert mark.main() == 0
    assert json.loads(capsys.readouterr().out.splitlines()[-1])["outputs"] == {"marked": 0}

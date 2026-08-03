"""Invoke `prompt-eval run` on the prompt packs whose steps ran this change.

This is the orchestrator side of the (ticket_id, change_id, step_id)
correlation key: prompt-optimizer stamps those three values onto every
results.jsonl row from the environment, so the row is only joinable back to a
ticket if this call site exports them.

step_id is exported *per pack* — the step whose prompt is being evaluated, not
this step's own id. Letting the engine's ORCHESTRATOR_STEP_ID ride through
would stamp every row `eval-prompts` and make the key useless.

Off unless ORCHESTRATOR_PROMPT_EVAL=1: evaluation invokes LLM judges.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def _emit(status: str, summary: str, packs: list[str] | None = None) -> None:
    print(json.dumps({
        "status": status,
        "outputs": {"prompt_eval": {"status": status, "packs": packs or []}},
        "evidence": {"summary": summary},
    }))


def _log(msg: str) -> None:
    print(f"eval-prompts: {msg}", file=sys.stderr)


def _load_state(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError:
        return {}


def ticket_id_from_state(state: dict) -> str:
    """Uppercased ticket_id, matching lib/ticket/ticket-sync.sh's normalization."""
    return str(state.get("ticket_id") or "").strip().upper()


def completed_step_ids(state: dict) -> list[str]:
    """Step ids that reached completed status, in first-seen order."""
    seen: list[str] = []
    for entry in state.get("step_history") or []:
        if not isinstance(entry, dict) or entry.get("status") != "completed":
            continue
        step_id = str(entry.get("step_id") or "")
        if step_id and step_id not in seen:
            seen.append(step_id)
    return seen


def _config_root() -> Path:
    """The config/ dir this step was dispatched from.

    Derived from ORCHESTRATOR_STEP_DIR (config/steps/<id>), which the engine
    always sets and script.sh already hard-requires. ORCHESTRATOR_CONFIG is
    only set when the caller exports it (paths.py), so it cannot be relied on
    here — an unset value would silently resolve zero packs.
    """
    step_dir = os.environ.get("ORCHESTRATOR_STEP_DIR") or ""
    if step_dir:
        return Path(step_dir).resolve().parent.parent
    return Path(os.environ.get("ORCHESTRATOR_CONFIG") or ".").resolve()


def _prompt_search_dirs(repo_root: str, config_root: Path) -> list[Path]:
    """Prompt search path: engine-exported ORCHESTRATOR_PROMPT_PATH when set,
    else <repo>/skills then <pack>/skills (sibling of config/)."""
    explicit = os.environ.get("ORCHESTRATOR_PROMPT_PATH") or os.environ.get(
        "ORCHESTRATOR_SKILLS_TEST_OVERRIDE"
    )
    if explicit:
        return [Path(p) for p in explicit.split(os.pathsep) if p]
    dirs: list[Path] = []
    if repo_root:
        dirs.append(Path(repo_root) / "skills")
    pack_skills = config_root.parent / "skills"
    if pack_skills not in dirs:
        dirs.append(pack_skills)
    return dirs


def _resolve_pack_dir(
    steps_root: Path, step_id: str, search_dirs: list[Path]
) -> Path | None:
    """Absolute pack dir for a prompt step, or None.

    Resolution order (first directory hit wins — a repo shadow without
    ``scenarios/`` means "do not evaluate", never fall through):

    1. ``<search_dir>/<step_id>`` (repo / override shadow by step id)
    2. Step-local ``prompt:`` file's parent (e.g. ``explore/SKILL.md`` symlink)
    3. ``<search_dir>/<prompt-parent>`` for legacy ``prompt: learn/SKILL.md``
    """
    for root in search_dirs:
        by_step = root / step_id
        if by_step.is_dir():
            return by_step.resolve()

    step_dir = steps_root / step_id
    try:
        with open(step_dir / "contract.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except OSError:
        return None
    ref = str(data.get("prompt") or "").strip()
    if not ref:
        return None
    local = step_dir / ref
    if local.is_file():
        return local.parent.resolve()
    parent = Path(ref).parent
    if str(parent) == ".":
        return None
    for root in search_dirs:
        candidate = root / parent
        if candidate.is_dir():
            return candidate.resolve()
    return None


def evaluable_packs(
    state: dict, config_root: Path, repo_root: str
) -> list[tuple[str, Path]]:
    """(step_id, pack_dir) for completed prompt steps whose pack has scenarios."""
    steps_root = config_root / "steps"
    search_dirs = _prompt_search_dirs(repo_root, config_root)
    packs: list[tuple[str, Path]] = []
    for step_id in completed_step_ids(state):
        pack_dir = _resolve_pack_dir(steps_root, step_id, search_dirs)
        if pack_dir is None:
            continue
        # Caller already received the first search hit; only evaluate when
        # that pack actually has scenarios/.
        if (pack_dir / "scenarios").is_dir():
            packs.append((step_id, pack_dir))
    return packs


def _eval_command() -> list[str] | None:
    """The `prompt-eval run` argv prefix, or None when unconfigured.

    ORCHESTRATOR_PROMPT_EVAL_BIN wins when set (tests point it at a stub);
    otherwise the prompt-optimizer checkout is run through uv, matching its
    README. There is deliberately no hardcoded absolute default: the checkout
    has no remote and lives at a machine-specific path.
    """
    override = os.environ.get("ORCHESTRATOR_PROMPT_EVAL_BIN") or ""
    if override:
        command = [override, "run"]
    else:
        optimizer_dir = os.environ.get("ORCHESTRATOR_PROMPT_OPTIMIZER_DIR") or ""
        if not optimizer_dir or not Path(optimizer_dir).is_dir():
            return None
        command = ["uv", "run", "--locked", "--project", optimizer_dir, "prompt-eval", "run"]

    # Budget passthrough. prompt-eval's own default split is `all`
    # (train+dev+holdout), so an enabled run is unbounded unless narrowed here.
    split = os.environ.get("ORCHESTRATOR_PROMPT_EVAL_SPLIT") or ""
    if split:
        command += ["--split", split]
    max_calls = os.environ.get("ORCHESTRATOR_PROMPT_EVAL_MAX_CALLS") or ""
    if max_calls:
        command += ["--max-external-calls", max_calls]
    return command


def main() -> int:
    if os.environ.get("ORCHESTRATOR_PROMPT_EVAL") != "1":
        _log("ORCHESTRATOR_PROMPT_EVAL is not 1 — skipping (evaluation costs judge calls)")
        _emit("completed", "prompt eval disabled (ORCHESTRATOR_PROMPT_EVAL != 1)")
        return 0

    command = _eval_command()
    if command is None:
        _log("ORCHESTRATOR_PROMPT_OPTIMIZER_DIR unset or missing — skipping")
        _emit("completed", "prompt-optimizer not configured")
        return 0

    state_path = os.environ.get("ORCHESTRATOR_STATE_YAML_PATH") or os.environ.get("STATE_YAML_PATH") or ""
    state = _load_state(state_path) if state_path else {}
    repo_root = os.environ.get("ORCHESTRATOR_REPO_ROOT") or os.environ.get("REPO_ROOT") or ""
    packs = evaluable_packs(state, _config_root(), repo_root)
    if not packs:
        _log("no completed prompt step has a pack with scenarios/ — nothing to evaluate")
        _emit("completed", "no evaluable packs")
        return 0

    ticket_id = ticket_id_from_state(state)
    if not ticket_id:
        _log("WARN state.yaml has no ticket_id — rows will not join back to a ticket")

    # Opt-in detach (ORCHESTRATOR_PROMPT_EVAL_ASYNC=1): evaluation writes only
    # the optimizer's results files — nothing downstream in the run reads them —
    # so it doesn't belong on the critical path (652s serial on BKG-575). The
    # step re-execs itself detached and completes immediately; the child's logs
    # land beside state.yaml in eval-prompts.log.
    if (
        os.environ.get("ORCHESTRATOR_PROMPT_EVAL_ASYNC") == "1"
        and os.environ.get("_EVAL_PROMPTS_DETACHED") != "1"
    ):
        log_path = (Path(state_path).parent if state_path else Path.cwd()) / "eval-prompts.log"
        with open(log_path, "ab") as log:
            subprocess.Popen(
                [sys.executable, os.path.abspath(__file__)],
                env={**os.environ, "_EVAL_PROMPTS_DETACHED": "1"},
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        pack_names = [pack_dir.name for _, pack_dir in packs]
        _emit("completed", f"evaluating {len(packs)} pack(s) detached; log: {log_path}", pack_names)
        return 0

    evaluated: list[str] = []
    for step_id, pack_dir in packs:
        env = dict(os.environ)
        env["ORCHESTRATOR_TICKET_ID"] = ticket_id
        # Per-pack: the step whose prompt this is, not this step's own id.
        env["ORCHESTRATOR_STEP_ID"] = step_id
        _log(f"evaluating {pack_dir.name} (step_id={step_id}, ticket_id={ticket_id or 'none'})")
        result = subprocess.run([*command, "--pack", str(pack_dir)], env=env)
        if result.returncode != 0:
            _log(f"WARN prompt-eval run failed for {pack_dir.name} (exit {result.returncode})")
            continue
        evaluated.append(pack_dir.name)

    _emit("completed", f"evaluated {len(evaluated)} pack(s)", evaluated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

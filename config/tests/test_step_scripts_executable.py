"""Every `config/steps/<id>/script.sh` must be executable in the git index.

A driver execs `payload.run_path` directly (no `bash`/`sh` wrapper), so a script
committed at mode 100644 fails with EACCES on every fresh checkout. The git
index mode is the source of truth: `git checkout` mirrors it onto disk, so a
local `chmod +x` that never reaches the index does not fix the consumer.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_CONFIG_ROOT = Path(__file__).resolve().parents[1]
_STEP_SCRIPT_PATHSPEC = "steps/*/script.sh"
_EXECUTABLE_MODE = "100755"


def _git_ls_files_staged() -> list[tuple[str, str]]:
    """Return (mode, path) for every tracked step script, or skip if git can't answer."""
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-s", "--", _STEP_SCRIPT_PATHSPEC],
            cwd=_CONFIG_ROOT,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - no git binary
        pytest.skip(f"git unavailable, cannot read index modes: {exc}")
    if proc.returncode != 0:  # pragma: no cover - pack checked out without git metadata
        pytest.skip(f"git ls-files failed (not a git checkout?): {proc.stderr.strip()}")

    entries = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # "<mode> <object> <stage>\t<path>"
        meta, _, path = line.partition("\t")
        entries.append((meta.split()[0], path))
    return entries


def test_step_scripts_are_executable_in_git_index():
    entries = _git_ls_files_staged()
    assert entries, (
        f"no tracked step scripts matched {_STEP_SCRIPT_PATHSPEC!r} under {_CONFIG_ROOT}; "
        "the pathspec is stale, so this test would pass vacuously"
    )

    offenders = [(mode, path) for mode, path in entries if mode != _EXECUTABLE_MODE]
    assert not offenders, (
        "step scripts must be mode 100755 in the git index (a driver execs "
        "payload.run_path directly); fix with `git update-index --chmod=+x <path>`: "
        + ", ".join(f"{path} is {mode}" for mode, path in offenders)
    )


def test_step_scripts_are_executable_on_disk():
    """Checkout mirrors the index mode — guard the working tree too (e.g. core.fileMode=false)."""
    scripts = sorted(_CONFIG_ROOT.glob(_STEP_SCRIPT_PATHSPEC))
    assert scripts, f"no step scripts found under {_CONFIG_ROOT / 'steps'}"

    not_executable = [str(p) for p in scripts if not os.access(p, os.X_OK)]
    assert not not_executable, (
        "step scripts must be executable on disk: " + ", ".join(not_executable)
    )

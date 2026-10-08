"""Pack scripts run Python via ${ORCHESTRATOR_PYTHON:-python3}; point them at the
interpreter running the tests, which has the pack's dependencies (PyYAML)."""
import os
import sys

os.environ.setdefault("ORCHESTRATOR_PYTHON", sys.executable)

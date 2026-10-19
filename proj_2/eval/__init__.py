"""M0 risk-killer eval (see docs/m0-eval.md).

The eval runs PackPlate's real filter engine, which lives in backend/app, so
backend/ goes on the import path here. That keeps the one command,
`python -m eval.m0` from proj_2/, working without extra setup.
"""

import sys
from pathlib import Path

_BACKEND = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

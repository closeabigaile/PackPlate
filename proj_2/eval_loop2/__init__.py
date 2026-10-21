"""M0 eval, loop 2 (pre-registered in #26): PackPlate after the ingredient flags.

Kept fully separate from loop 1 (eval/): it never imports it, so either loop
can be removed without touching the other. Small pieces that loop 1 also has
(the test profiles, the group simulator) are copied here on purpose.

Like loop 1, it runs PackPlate's real filter engine from backend/app, so
backend/ goes on the import path here.
"""

import sys
from pathlib import Path

_BACKEND = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

"""Load loop 2's frozen snapshot and run today's PackPlate filter on it.

"Today's PackPlate" means what the API does: approved label reviews are applied
with the backend's own `reviewed()`, and the filter reads the stored ingredient
flags along with NC State's icons and labels.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from app.services import filter_engine
from app.services.label_reviews import reviewed

SNAPSHOT = Path(__file__).parent / "data" / "snapshot.json"


def load(path: Path = SNAPSHOT) -> dict:
    """The frozen snapshot, as written by eval_loop2/export_snapshot.py."""
    return json.loads(path.read_text(encoding="utf-8"))


def approved_reviews(snapshot: dict) -> dict:
    """The snapshot's approved reviews, keyed the way `reviewed()` looks them up."""
    return {
        (r["location_id"], r["dish"], r["ingredients_hash"]): (r["tags"], r["reason"])
        for r in snapshot["reviews"]
    }


def packplate_item(item: dict, location_id: int, snapshot: dict, approved: dict):
    """A snapshot item as the API hands it to the filter, with reviews applied."""
    label = snapshot["labels"][item["label"]] if item["label"] else None
    raw = SimpleNamespace(
        id=item["id"],
        name=item["name"],
        course=item["course"],
        serving_size=label["serving_size"] if label else None,
        allergens=item["allergens"],
        diets=item["diets"],
        unrecognized_traits=item["unrecognized_traits"],
        nutrition=SimpleNamespace(**label) if label else None,
    )
    return reviewed(raw, location_id, approved)


def verdict(item: dict, location_id: int, snapshot: dict, approved: dict, profile):
    """Today's PackPlate verdict for one snapshot item and one profile."""
    view = packplate_item(item, location_id, snapshot, approved)
    return filter_engine.check(view, profile).verdict

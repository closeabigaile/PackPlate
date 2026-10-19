"""Load the frozen snapshot and run both filters on it."""

import json
from pathlib import Path
from types import SimpleNamespace

from app.services import filter_engine
from eval import baseline

SNAPSHOT = Path(__file__).parent / "data" / "snapshot.json"


def load(path: Path = SNAPSHOT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def packplate_item(item: dict, labels: dict) -> SimpleNamespace:
    """A snapshot item in the shape PackPlate's filter engine reads."""
    label = labels[item["label"]] if item["label"] else None
    return SimpleNamespace(
        allergens=item["allergens"],
        diets=item["diets"],
        unrecognized_traits=item["unrecognized_traits"],
        nutrition=(
            SimpleNamespace(
                protein_g=label["protein_g"],
                calories=label["calories"],
                sodium_mg=label["sodium_mg"],
            )
            if label
            else None
        ),
    )


def verdicts(item: dict, labels: dict, profile) -> tuple[str, str]:
    """(PackPlate's verdict, the icon-only baseline's verdict) for one item."""
    ours = filter_engine.check(packplate_item(item, labels), profile).verdict
    return ours, baseline.check(item["icons"], profile)

"""Simulated groups for M0's "Useful" claim. These are simulated users, not real ones.

Each group is 2-5 people at one of the snapshot's mealtimes. Each person
independently gets each allergy (and halal) with the probability in
eval/simulation.json, and one diet: vegan, vegetarian, or none. Most people end up
with no restriction at all, as in real life. A fixed seed makes the same groups
every run.
"""

import json
import random
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

from app.services.filter_engine import Profile
from app.services.hours import CAMPUS_TZ

# Not "config.json": the root .gitignore ignores every file with that name.
CONFIG = Path(__file__).parent / "simulation.json"


@dataclass(frozen=True)
class Group:
    """One simulated group: when and at which meal they eat, and each person's needs."""

    at: datetime  # campus time
    meal: str  # the meal menu served at `at`: Breakfast / Lunch / Dinner
    people: tuple[Profile, ...]


def load_config(path: Path = CONFIG) -> dict:
    """The simulation settings in eval/simulation.json."""
    return json.loads(path.read_text(encoding="utf-8"))


def person(rng: random.Random, config: dict) -> Profile:
    """One simulated person, drawn with the probabilities in `config`."""
    avoid = frozenset(
        key for key, spec in sorted(config["avoid"].items()) if rng.random() < spec["p"]
    )
    diets = set()
    if rng.random() < config["halal"]["p"]:
        diets.add("halal")
    roll = rng.random()
    if roll < config["diet"]["vegan"]:
        diets.add("vegan")
    elif roll < config["diet"]["vegan"] + config["diet"]["vegetarian"]:
        diets.add("vegetarian")
    return Profile(avoid=avoid, diets=frozenset(diets))


def groups(config: dict) -> list[Group]:
    """All the simulated groups. The same seed always gives the same groups."""
    rng = random.Random(config["seed"])
    low, high = config["group_size"]
    slots = [
        (date.fromisoformat(day), clock, meal)
        for day in config["days"]
        for clock, meal in config["times"].items()
    ]
    out = []
    for _ in range(config["groups"]):
        day, clock, meal = rng.choice(slots)
        at = datetime.combine(day, time.fromisoformat(clock), CAMPUS_TZ)
        size = rng.randint(low, high)
        out.append(Group(at, meal, tuple(person(rng, config) for _ in range(size))))
    return out

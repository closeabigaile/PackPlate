"""The simulated groups: fixed by the seed, shaped by the cited config."""

import random
from datetime import date

import pytest

from app.services.filter_engine import ALLERGEN_KEYS, DIET_KEYS
from eval.simulate import groups, load_config, person

CONFIG = load_config()


def test_config_matches_the_pre_registration():
    assert CONFIG["days"] == ["2026-10-12", "2026-10-13", "2026-10-14"]
    assert CONFIG["group_size"] == [2, 5]
    assert CONFIG["times"] == {
        "08:00": "Breakfast",
        "12:30": "Lunch",
        "18:00": "Dinner",
    }


def test_every_restriction_has_a_probability_and_a_source():
    assert set(CONFIG["avoid"]) == set(ALLERGEN_KEYS)
    for spec in [*CONFIG["avoid"].values(), CONFIG["halal"], CONFIG["diet"]]:
        assert spec["source"] and spec["quote"]
    for p in [s["p"] for s in CONFIG["avoid"].values()] + [CONFIG["halal"]["p"]]:
        assert 0 < p < 0.1
    assert 0 < CONFIG["diet"]["vegan"] + CONFIG["diet"]["vegetarian"] < 0.1


def test_same_seed_same_groups():
    assert groups(CONFIG) == groups(CONFIG)


def test_different_seed_different_groups():
    assert groups(CONFIG) != groups({**CONFIG, "seed": CONFIG["seed"] + 1})


def test_groups_use_only_the_snapshot_days_and_mealtimes():
    gs = groups(CONFIG)
    assert len(gs) == CONFIG["groups"]
    days = {date.fromisoformat(d) for d in CONFIG["days"]}
    for g in gs:
        assert g.at.date() in days
        assert g.at.strftime("%H:%M") in CONFIG["times"]
        assert g.meal == CONFIG["times"][g.at.strftime("%H:%M")]
        assert 2 <= len(g.people) <= 5
        assert str(g.at.tzinfo) == "America/New_York"


def test_every_group_size_and_time_slot_occurs():
    gs = groups(CONFIG)
    assert {len(g.people) for g in gs} == {2, 3, 4, 5}
    assert len({g.at for g in gs}) == len(CONFIG["days"]) * len(CONFIG["times"])


def test_people_only_use_keys_packplate_knows():
    for g in groups(CONFIG):
        for p in g.people:
            assert p.avoid <= set(ALLERGEN_KEYS)
            assert p.diets <= set(DIET_KEYS)
            assert not {"vegan", "vegetarian"} <= p.diets


def rates(n=200_000):
    rng = random.Random(1)
    people = [person(rng, CONFIG) for _ in range(n)]
    share = {a: sum(a in p.avoid for p in people) / n for a in ALLERGEN_KEYS}
    share |= {d: sum(d in p.diets for p in people) / n for d in DIET_KEYS}
    share["none"] = sum(not p.avoid and not p.diets for p in people) / n
    return share


RATES = rates()


@pytest.mark.parametrize("allergen", ALLERGEN_KEYS)
def test_allergy_rates_match_the_config(allergen):
    assert RATES[allergen] == pytest.approx(CONFIG["avoid"][allergen]["p"], abs=0.002)


def test_diet_rates_match_the_config():
    assert RATES["halal"] == pytest.approx(CONFIG["halal"]["p"], abs=0.002)
    assert RATES["vegan"] == pytest.approx(CONFIG["diet"]["vegan"], abs=0.002)
    assert RATES["vegetarian"] == pytest.approx(CONFIG["diet"]["vegetarian"], abs=0.002)


def test_most_people_have_no_restriction():
    assert RATES["none"] > 0.8

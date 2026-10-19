"""The eleven M0 test profiles, as fixed in the pre-registration issue:
one per allergen PackPlate knows and one per diet."""

from app.services.filter_engine import ALLERGEN_KEYS, DIET_KEYS, Profile

TEST_PROFILES = {
    **{f"avoid_{a}": Profile(avoid=frozenset({a})) for a in ALLERGEN_KEYS},
    **{f"diet_{d}": Profile(diets=frozenset({d})) for d in DIET_KEYS},
}

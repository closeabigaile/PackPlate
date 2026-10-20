"""The eleven test profiles: one per allergen PackPlate knows and one per diet.

The same profiles as loop 1 (#11), as #26 says. Copied rather than imported, so
loop 2 never depends on loop 1's code.
"""

from app.services.filter_engine import ALLERGEN_KEYS, DIET_KEYS, Profile

TEST_PROFILES = {
    **{f"avoid_{a}": Profile(avoid=frozenset({a})) for a in ALLERGEN_KEYS},
    **{f"diet_{d}": Profile(diets=frozenset({d})) for d in DIET_KEYS},
}

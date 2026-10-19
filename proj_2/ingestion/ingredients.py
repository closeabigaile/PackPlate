"""Possible allergens: what an item's ingredient text mentions.

NC State's icons and "Contains:" line sometimes leave out an allergen the
ingredients name (M0 eval, issue #15). This scan finds those words so the filter
can mark the item "incomplete" instead of "fits". A hit is only a possibility,
never a confirmed allergen: it is stored apart from NC State's allergens.

Deterministic: the same text always gives the same sorted keys. Matching is
whole words, any case, with an optional plural "s"/"es".

Sources for each key are noted next to its words. Cross-contact warnings ("may
contain", "made in a facility that also processes ...") are not ingredients and
are ignored. Halal is not scanned beyond pork: there is no single standard for
it (certifiers differ on alcohol and gelatin sources).

The words started from eval/wordlist.py but are kept here on purpose, so the M0
eval stays an independent check of this scan.
"""

import re

# Keys match normalize.ALLERGEN_KEYS, plus "meat" and "honey" for diet checks.
WORDS = {
    # FDA major allergen "milk" (21 U.S.C. 321(qq)), which includes milk from
    # goats, sheep, and other ruminants (FDA allergen guidance, Edition 5, 2025).
    "dairy": [
        "milk", "butter", "buttermilk", "cream", "cheese", "whey", "casein",
        "caseinate", "lactose", "yogurt", "yoghurt", "ghee", "kefir", "curd",
        "custard", "parmesan", "mozzarella", "cheddar", "ricotta", "provolone",
        "feta", "gouda", "romano", "asiago", "mascarpone", "paneer", "chevre",
        "chèvre", "half and half",
    ],
    # FDA major allergen "egg", which includes eggs from chickens, ducks, geese,
    # quail, and other fowl (FDA allergen guidance, Edition 5, 2025).
    "egg": ["egg", "egg white", "egg yolk", "albumen", "albumin", "mayonnaise", "meringue"],
    # Gluten-containing grains (21 CFR 101.91): wheat (any Triticum species, e.g.
    # durum, spelt, kamut/khorasan, einkorn, emmer/farro), rye, barley, and their
    # hybrids (triticale). Plain "flour" is wheat flour (21 CFR 137.105).
    "gluten": [
        "wheat", "gluten", "barley", "rye", "malt", "semolina", "durum", "spelt",
        "kamut", "khorasan", "einkorn", "emmer", "farro", "couscous", "bulgur",
        "seitan", "triticale", "flour",
    ],
    # FDA major allergens "peanuts" and "tree nuts"; tree nuts are the 12 in Table 1
    # of the FDA allergen guidance, Edition 5 (2025). Coconut, chestnut, and other
    # nuts removed from that list are deliberately absent.
    "nuts": [
        "nut", "tree nut", "peanut", "almond", "black walnut", "brazil nut",
        "cashew", "filbert", "hazelnut", "heartnut", "macadamia", "bush nut",
        "pecan", "pine nut", "pinon", "piñon", "pistachio", "walnut", "praline",
        "marzipan",
    ],
    # NC State's "Contains Pork" category; pork is also the one ingredient every
    # halal standard excludes.
    "pork": [
        "pork", "bacon", "ham", "prosciutto", "pancetta", "lard", "chorizo",
        "pepperoni", "salami",
    ],
    # FDA major allergens "fish" and "crustacean shellfish", plus molluscs, to
    # match NC State's "Contains Seafood" category.
    "seafood": [
        "fish", "shellfish", "anchovy", "anchovies", "tuna", "salmon", "cod",
        "tilapia", "pollock", "catfish", "haddock", "swai", "sardine", "flounder",
        "shrimp", "prawn", "crab", "lobster", "crayfish", "clam", "oyster",
        "scallop", "mussel", "squid", "calamari",
    ],
    # FDA major allergen "sesame" (FASTER Act, 2021).
    "sesame": ["sesame", "tahini"],
    # FDA major allergen "soybeans". Highly refined oils are exempt (21 U.S.C.
    # 321(qq)(2)(A)); see EXCEPT.
    "soy": ["soy", "soya", "soybean", "tofu", "edamame", "miso", "tempeh", "tamari"],
    # Not vegetarian: meat, poultry ("meat, fish and chicken", Vegetarian Society;
    # fish is under "seafood") and slaughter by-products such as gelatin and tallow.
    "meat": [
        "beef", "chicken", "turkey", "lamb", "veal", "duck", "meat", "sausage",
        "gelatin", "gelatine", "tallow",
    ],
    # Not vegan (Vegan Society): honey. Dairy, egg, meat, and seafood are above.
    "honey": ["honey"],
}  # fmt: skip

# Phrases removed before matching: they contain a word above but aren't that allergen.
EXCEPT = [
    # dairy look-alikes
    "coconut milk", "almond milk", "oat milk", "soy milk", "soymilk", "rice milk",
    "cocoa butter", "peanut butter", "nut butter", "almond butter", "cashew butter",
    "sunflower butter", "seed butter", "apple butter", "shea butter",
    "cream of tartar", "coconut cream",
    # the dairy-free shred inside NC State's "Vegan Mozzarella" (no milk in it)
    "mozzarella style shred",
    # flours not made from a gluten-containing grain
    "rice flour", "corn flour", "potato flour", "almond flour", "coconut flour",
    "chickpea flour", "tapioca flour", "cassava flour", "oat flour", "sorghum flour",
    "buckwheat flour", "gluten free flour", "gluten friendly",
    # pork look-alikes
    "turkey bacon", "beef bacon", "turkey ham", "turkey pepperoni", "beef pepperoni",
    "turkey salami", "chicken chorizo",
    # eggs from other fowl are egg, not meat
    "duck egg", "goose egg", "quail egg", "turkey egg",
    # highly refined soybean oil is exempt (21 U.S.C. 321(qq)(2)(A)); assumed refined
    "soybean oil", "soy oil",
]  # fmt: skip

# Look-alikes that still contain a different allergen: replaced by that word.
_RESTORE = {
    "peanut butter": "peanut", "almond butter": "almond", "cashew butter": "cashew",
    "nut butter": "nut", "almond milk": "almond", "almond flour": "almond",
    "soy milk": "soy", "soymilk": "soy", "duck egg": "egg", "goose egg": "egg",
    "quail egg": "egg", "turkey egg": "egg",
}  # fmt: skip

_ADVISORY = re.compile(
    r"(may contain|in a facility|on shared equipment|on equipment that|"
    r"same equipment|made in a plant)[^.)]*",
    re.I,
)
_FREE_OF = re.compile(r"\b[a-z]+[- ]free\b|\bnon-?dairy\b", re.I)

# Plant-based modifiers and the plant-based brands that appear in NC State's
# ingredient text. An animal-product word directly after one ("Vegan Mozzarella",
# "Plant-Based Beef", "Impossible Sausage") names an imitation, so it is skipped.
# Only the very next word: "Vegan Pesto with Cheese" is still flagged.
PLANT_BASED = [
    "vegan", "vegetarian", "veggie", "plant-based", "plant based", "meatless",
    "meat-free", "dairy-free", "impossible", "beyond",
]  # fmt: skip
_ANIMAL_KEYS = ("dairy", "egg", "meat", "pork", "seafood", "honey")
_ANIMAL_WORDS = sorted(
    {t for k in _ANIMAL_KEYS for t in WORDS[k] if " " not in t}, key=len, reverse=True
)
_IMITATION = re.compile(
    r"\b("
    + "|".join(r"[\s-]+".join(map(re.escape, m.split())) for m in PLANT_BASED)
    + r")[\s-]+(?:"
    + "|".join(map(re.escape, _ANIMAL_WORDS))
    + r")(?:e?s)?\b",
    re.I,
)


def _pattern(term: str) -> re.Pattern:
    """Whole words, any case, optional plural; spaces also match hyphens."""
    words = r"[\s-]+".join(re.escape(w) for w in term.split())
    return re.compile(rf"\b{words}(?:e?s)?\b", re.I)


_TERMS = {key: [_pattern(t) for t in terms] for key, terms in WORDS.items()}
_EXCEPT = [(_pattern(e), _RESTORE.get(e, "")) for e in EXCEPT]


def possible_allergens(ingredients: str | None) -> list[str]:
    """Keys the ingredient text mentions, sorted. [] if none or no text."""
    if not ingredients:
        return []
    text = _ADVISORY.sub(" ", ingredients)
    text = _IMITATION.sub(r" \1 ", text)
    for pattern, keep in _EXCEPT:
        text = pattern.sub(f" {keep} ", text)
    text = _FREE_OF.sub(" ", text)
    return sorted(
        key for key, patterns in _TERMS.items() if any(p.search(text) for p in patterns)
    )

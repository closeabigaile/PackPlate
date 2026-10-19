"""Ingredient words that mean an item breaks a test profile. Reviewed by a human.

For each test profile: `terms` that flag an item, and `except_` phrases that are
removed before matching because they look like a term but aren't one (cocoa
butter isn't dairy). Matching ignores case, needs whole words, and also matches
a plural "s" / "es". A flag is only a lead: a person confirms or rejects every
one in the spot-check.

Deliberately left out, and listed as limits in the results:
- "natural flavors", "spices", "seasoning": can hide an allergen, but the text
  doesn't say which.
- coconut: not counted as a nut here; NC State's "Contains Nuts" covers peanuts
  and tree nuts and doesn't say how it treats coconut.
- oats: often contaminated with gluten, but not a gluten ingredient.
- vanilla extract and other flavor extracts: contain alcohol, but whether that
  matters for halal is disputed.
- Meat that isn't pork can't be shown to be non-halal from ingredients.
"""

DAIRY = [
    "milk", "butter", "buttermilk", "cream", "cheese", "whey", "casein",
    "caseinate", "lactose", "yogurt", "yoghurt", "ghee", "kefir", "curd",
    "custard", "parmesan", "mozzarella", "cheddar", "ricotta", "provolone",
    "feta", "gouda", "romano", "asiago", "mascarpone", "paneer", "half and half",
]  # fmt: skip
DAIRY_EXCEPT = [
    "coconut milk", "almond milk", "oat milk", "soy milk", "soymilk",
    "rice milk", "cocoa butter", "peanut butter", "nut butter", "almond butter",
    "cashew butter", "sunflower butter", "seed butter", "apple butter",
    "shea butter", "cream of tartar", "coconut cream", "vegan cheese",
]  # fmt: skip

EGG = ["egg", "egg white", "egg yolk", "albumen", "albumin", "mayonnaise", "meringue"]

GLUTEN = [
    "wheat", "gluten", "barley", "rye", "malt", "semolina", "durum", "spelt",
    "farro", "couscous", "bulgur", "seitan", "triticale", "flour",
]  # fmt: skip
GLUTEN_EXCEPT = [
    "rice flour", "corn flour", "potato flour", "almond flour", "coconut flour",
    "chickpea flour", "tapioca flour", "cassava flour", "oat flour",
    "sorghum flour", "buckwheat flour", "gluten free flour", "gluten friendly",
]  # fmt: skip

NUTS = [
    "nut", "peanut", "almond", "cashew", "pecan", "walnut", "pistachio",
    "hazelnut", "filbert", "macadamia", "brazil nut", "pine nut", "praline",
    "marzipan",
]  # fmt: skip

PORK = [
    "pork", "bacon", "ham", "prosciutto", "pancetta", "lard", "chorizo",
    "pepperoni", "salami",
]  # fmt: skip
PORK_EXCEPT = [
    "turkey bacon", "beef bacon", "turkey ham", "turkey pepperoni",
    "beef pepperoni", "turkey salami", "chicken chorizo",
]  # fmt: skip

SEAFOOD = [
    "fish", "shellfish", "anchovy", "anchovies", "tuna", "salmon", "cod",
    "tilapia", "pollock", "catfish", "haddock", "swai", "sardine", "shrimp",
    "crab", "lobster", "clam", "oyster", "scallop", "mussel", "squid",
    "calamari", "worcestershire",
]  # fmt: skip

SESAME = ["sesame", "tahini"]

SOY = ["soy", "soya", "soybean", "tofu", "edamame", "miso", "tempeh", "tamari"]
SOY_EXCEPT = ["soybean oil", "soy oil"]  # highly refined oils are exempt by law

MEAT = [
    "beef", "chicken", "turkey", "lamb", "veal", "duck", "meat", "sausage",
    "gelatin", "tallow",
]  # fmt: skip

ALCOHOL = [
    "wine", "beer", "rum", "bourbon", "brandy", "whiskey", "whisky", "vodka",
    "sake", "mirin", "liqueur", "sherry", "marsala",
]  # fmt: skip
ALCOHOL_EXCEPT = [
    "wine vinegar", "red wine vinegar", "white wine vinegar", "rice wine vinegar",
    "sherry vinegar",
]  # fmt: skip

WORDS = {
    "avoid_dairy": {"terms": DAIRY, "except_": DAIRY_EXCEPT},
    "avoid_egg": {"terms": EGG, "except_": []},
    "avoid_gluten": {"terms": GLUTEN, "except_": GLUTEN_EXCEPT},
    "avoid_nuts": {"terms": NUTS, "except_": []},
    "avoid_pork": {"terms": PORK, "except_": PORK_EXCEPT},
    "avoid_seafood": {"terms": SEAFOOD, "except_": []},
    "avoid_sesame": {"terms": SESAME, "except_": []},
    "avoid_soy": {"terms": SOY, "except_": SOY_EXCEPT},
    "diet_vegetarian": {"terms": MEAT + PORK + SEAFOOD, "except_": []},
    "diet_vegan": {
        "terms": MEAT + PORK + SEAFOOD + DAIRY + EGG + ["honey"],
        "except_": DAIRY_EXCEPT,
    },
    "diet_halal": {
        "terms": PORK + ALCOHOL + ["gelatin"],
        "except_": PORK_EXCEPT + ALCOHOL_EXCEPT,
    },
}

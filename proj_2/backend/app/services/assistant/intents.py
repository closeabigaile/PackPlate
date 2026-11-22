"""Understand a student's message (M3).

Turns free text into an Intent: what kind of question it is, which location,
meal and day it mentions, and any restrictions or nutrition goals typed in the
message. Pure functions, no database: the caller passes in the location names.

This is the rule-based understanding step. An optional language model can later
replace parse() and return the same Intent, and nothing after it changes.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

# Allergen keys must match services/filter_engine.py ALLERGEN_KEYS.
ALLERGEN_WORDS = {
    "dairy": ("dairy", "milk", "lactose"),
    "egg": ("egg", "eggs"),
    "gluten": ("gluten", "wheat"),
    "nuts": ("nut", "nuts", "peanut", "peanuts"),
    "pork": ("pork",),
    "seafood": ("seafood", "fish", "shellfish"),
    "sesame": ("sesame",),
    "soy": ("soy",),
}
DIET_WORDS = ("halal", "vegan", "vegetarian")
HIGH_PROTEIN_G = 30  # what "high protein" means when no number is given

_WORD_TO_ALLERGEN = {w: key for key, words in ALLERGEN_WORDS.items() for w in words}
_ANY_ALLERGEN = "|".join(sorted(_WORD_TO_ALLERGEN, key=len, reverse=True))
_AVOID = re.compile(
    rf"\b(?:no|without|avoid|skip|free of|allergic to)\s+(?:any\s+)?({_ANY_ALLERGEN})\b"
)
_FREE = re.compile(rf"\b({_ANY_ALLERGEN})[- ]free\b")
_ALLERGY = re.compile(rf"\b({_ANY_ALLERGEN})\s+allerg\w*")

_HIGH_PROTEIN = re.compile(
    r"\b(?:high|extra)[- ]protein\b|\bprotein[- ]rich\b|\blots of protein\b|\bhigh in protein\b"
)
_PROTEIN_G = re.compile(r"\b(\d{1,3})\s*(?:g|grams?)\s*(?:of\s+)?protein\b")
_MAX_CALORIES = re.compile(
    r"\b(?:under|below|less than|max(?:imum)?(?: of)?|at most|up to|within)\s*"
    r"(\d{2,4})\s*(?:cal|kcal|calories?)\b"
)

MEAL_WORDS = ("late night", "breakfast", "brunch", "lunch", "dinner")

_MEDICAL = re.compile(
    r"\b(medical|medicine|medication|diagnos\w*|symptoms?|treat(?:ment)?|cure|"
    r"diabet\w*|pregnan\w*|doctor|dosage|epipen|anaphyla\w*|reaction)\b"
)
_SAFETY = re.compile(r"\b(safe|safely|guarantee\w*|risk[- ]free)\b")
_CROWD = re.compile(r"\b(busy|crowd(?:ed)?|packed|lines?|wait|queue|quiet|slammed)\b")
_STATUS = re.compile(r"\b(open|opens|closes?|closing|closed|hours)\b")
_FOOD = re.compile(
    r"\b(menu|eat|food|serving|serves?|dish(?:es)?|options?|hungry|protein|"
    r"calories?|kcal|vegan|vegetarian|halal)\b"
)
_HELP = re.compile(r"\b(help|hello|hi|hey)\b|what can you do")
# "Where can I eat right now?" asks for somewhere to go, not for a menu.
_WHERE_TO_EAT = re.compile(
    r"\bwhere\s+(?:can|should|could|do|shall)\s+(?:i|we)\s+(?:eat|get\s+(?:food|lunch|dinner|breakfast|something)|grab)"
)
_RECOMMEND = re.compile(r"\b(recommend\w*|suggest\w*|best|favou?rite)\b")
# Asking about distance. Not the bare word "close": "when does it close?" is about hours.
_NEARBY = re.compile(
    r"\b(closest|closer|nearest|nearby|near|is close|are close|"
    r"close to|how far|walking distance|walk from|distance)\b"
)
# Words that ask for a count or a list, and words that mean "a dining place".
_LISTING = re.compile(r"\b(how many|list|all|are there|which)\b")
_PLACE_WORDS = {"hall", "halls", "location", "locations", "place", "places"}

# Words in a location's name that don't tell locations apart.
_GENERIC_NAME_WORDS = {"dining", "hall", "the", "and", "of", "cafe"}
_NOT_A_PLACE = {"least", "most", "night", "noon", "home", "school", "campus"}
_PLACE_PHRASE = re.compile(
    r"\b(?:at|in|from)\s+((?:the\s+)?[a-z][a-z'\- ]*?)"
    r"(?=\s+(?:tonight|today|tomorrow|for|right|now|with|that|and|please|this|on)\b"
    r"|[?.!,]|$)"
)


@dataclass(frozen=True)
class Intent:
    """What a message asks for. Unset fields are None or empty, never guesses."""

    # food, status, crowd, locations, recommend, nearby, safety, medical, help, or unknown
    kind: str
    location_text: str | None = None  # a location name, or what was typed after "at"
    meal: str | None = None  # breakfast, brunch, lunch, dinner, late night
    day_offset: int = 0  # 0 = today, 1 = tomorrow
    diets: frozenset[str] = frozenset()
    avoid: frozenset[str] = frozenset()
    min_protein_g: float | None = None
    max_calories: float | None = None


def _meal(text: str) -> str | None:
    """The meal the message names ("dinner"), or one implied by "tonight" or "this morning"."""
    # If several meals are named, the one mentioned first wins.
    found = [(text.find(w), w) for w in MEAL_WORDS if re.search(rf"\b{w}\b", text)]
    if found:
        return min(found)[1]
    if re.search(r"\btonight\b", text):
        return "dinner"
    if re.search(r"\b(this )?morning\b", text):
        return "breakfast"
    return None


def _avoid(text: str) -> frozenset[str]:
    """Allergen keys the message asks to avoid: "no dairy", "gluten-free", "peanut allergy"."""
    words = _AVOID.findall(text) + _FREE.findall(text) + _ALLERGY.findall(text)
    return frozenset(_WORD_TO_ALLERGEN[w] for w in words)


def _protein(text: str) -> float | None:
    """A minimum protein in grams: a number if given ("40 g protein"), else a default for "high protein"."""
    if match := _PROTEIN_G.search(text):
        return float(match.group(1))
    return float(HIGH_PROTEIN_G) if _HIGH_PROTEIN.search(text) else None


def _calories(text: str) -> float | None:
    """A calorie limit from phrases like "under 600 calories", or None if none is given."""
    match = _MAX_CALORIES.search(text)
    return float(match.group(1)) if match else None


def _name_in(text: str, names: list[str]) -> str | None:
    """The one location whose name (or a telling word of it) the text mentions."""
    # Compare whole words only, so "case" matches the word "case" but not "showcase".
    words = set(re.findall(r"[a-z0-9']+", text))
    # A full name in the text settles it, even if a word of it fits other names too
    # ("Atrium – Brickyard Pizza" also contains "atrium", as "Atrium – Smoothie U" does).
    full = [name for name in names if name.casefold() in text]
    if full:
        return max(full, key=len)
    mentioned, shared = [], None
    for name in names:
        parts = [
            w
            for w in re.findall(r"[a-z0-9']+", name.casefold())
            if w not in _GENERIC_NAME_WORDS and len(w) >= 4
        ]
        hit = next((p for p in parts if p in words), None)
        if hit:
            mentioned.append(name)
            shared = shared or hit
    if len(mentioned) == 1:
        return mentioned[0]
    # Several fit one word ("atrium", "talley"): hand that word on, so the assistant
    # asks which one is meant instead of answering about a place from earlier.
    return shared if mentioned else None


def _phrase_after_at(text: str) -> str | None:
    """What was typed after "at", "in" or "from" ("menu at fountian"), for locations not matched by name."""
    match = _PLACE_PHRASE.search(text)
    if not match:
        return None
    phrase = match.group(1).strip()
    if not phrase or phrase in _NOT_A_PLACE or phrase in MEAL_WORDS:
        return None
    return phrase


# "I'm at Cox Hall, which...", "near the library", "closest dining hall to Lee Hall".
_WHERE = re.compile(
    r"\b(?:(?:i'?m|i am|im)\s+(?:currently\s+)?(?:at|in|near|by|on|outside|inside)"
    r"|(?:at|in|near|by|around|next to|close to|closest to|nearest to)"
    r"|(?:closest|nearest|close|near)(?:\s+(?:dining\s+)?(?:halls?|places?|locations?))?\s+to)"
    r"\s+(?:the\s+)?([a-z0-9][a-z0-9.'\- ]*?)"
    r"(?=\s+(?:which|what|where|how|is|are|can|do|does|please|and|for)\b|[,?.!;]|$)"
)
# What is not a place a student could be at: pronouns, directions, "the dining hall".
_NOT_WHERE = {"me", "here", "there", "my location", "campus", "main campus", "school"}
_NOT_WHERE_WORDS = {
    "dining",
    "hall",
    "halls",
    "place",
    "places",
    "location",
    "locations",
}


def where_phrase(text: str) -> str | None:
    """The place a student says they are at or near, as typed, or None.

    "I'm at Cox Hall, which dining hall is close?" gives "cox hall". It only cuts
    the text out; whether the place is real is for campus_places.json or the
    online lookup to say.
    """
    text = " ".join(text.casefold().split())
    for match in _WHERE.finditer(text):
        phrase = match.group(1).strip(" .'-")
        words = set(phrase.split())
        if not phrase or phrase in _NOT_WHERE or phrase in MEAL_WORDS:
            continue
        if words <= _NOT_WHERE_WORDS or len(phrase) < 3:
            continue
        return phrase
    return None


def _mentions_places(text: str) -> bool:
    """Whether the text talks about dining halls or locations, allowing a misspelled "dining"."""
    return any(
        word in _PLACE_WORDS or SequenceMatcher(None, word, "dining").ratio() >= 0.75
        for word in re.findall(r"[a-z]+", text)
    )


def _kind(text: str, meal, diets, avoid, protein, calories) -> str:
    """What sort of question this is. The order matters: the first rule that matches wins."""
    # Medical and "is it safe" questions come first, so nothing below can answer them.
    if _MEDICAL.search(text):
        return "medical"
    if _SAFETY.search(text):
        return "safety"
    # "I'm at Talley, which hall is close?" is about distance, not about a place
    # called "Talley, which hall is close".
    if _NEARBY.search(text):
        return "nearby"
    if _CROWD.search(text):
        return "crowd"
    if _WHERE_TO_EAT.search(text):
        return "recommend"
    # Food words, a diet, an allergen, or a nutrition goal all make this a food question.
    # "What's open for dinner?" stays a status question because it names no food need.
    wants_food = bool(
        _FOOD.search(text) or diets or avoid or protein or calories is not None
    )
    if _STATUS.search(text) and not wants_food:
        return "status"
    # "Which hall do you recommend?" and "how many dining halls are there?" name no food.
    if not wants_food and _RECOMMEND.search(text):
        return "recommend"
    if not wants_food and _LISTING.search(text) and _mentions_places(text):
        return "locations"
    if wants_food or meal:
        return "food"
    if _HELP.search(text):
        return "help"
    return "unknown"


def parse(text: str, location_names: list[str] | tuple[str, ...] = ()) -> Intent:
    """Read one message. `location_names` are the locations the app knows."""
    # Lowercase and collapse spaces once, so every rule above reads the same text.
    text = " ".join(text.casefold().split())
    meal = _meal(text)
    diets = frozenset(d for d in DIET_WORDS if re.search(rf"\b{d}\b", text))
    avoid = _avoid(text)
    protein = _protein(text)
    calories = _calories(text)
    # A location named in the text wins; otherwise use whatever followed "at".
    return Intent(
        kind=_kind(text, meal, diets, avoid, protein, calories),
        location_text=_name_in(text, list(location_names)) or _phrase_after_at(text),
        meal=meal,
        day_offset=1 if re.search(r"\btomorrow\b", text) else 0,
        diets=diets,
        avoid=avoid,
        min_protein_g=protein,
        max_calories=calories,
    )

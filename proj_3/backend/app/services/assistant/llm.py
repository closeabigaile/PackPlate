"""The optional language model layer (M3): a local Ollama server.

The model has one job: read a message the rules couldn't ("im starving, what can
i get?") and say what kind of question it is. It never writes text for the
student. Every word of every reply still comes from answers.py, and every fact
from the database tools.

That limit is deliberate. A small local model will confidently invent dishes and
places, so nothing it says is shown. What it returns is checked before use:
the kind and the diet/allergen keys must be known ones, goals must be numbers in
range, and a location is kept only if the student actually mentioned it.

If the model is off, unreachable, slow, or returns something unusable,
understand() returns None and the rule-based assistant answers instead.
"""

import json
import urllib.request
from dataclasses import replace

from app.services.assistant import intents, settings

# What the model may classify a message as. "medical" and "safety" get the same
# fixed replies as when the rules spot them.
ALLOWED_KINDS = {
    "food",
    "status",
    "crowd",
    "locations",
    "recommend",
    "nearby",
    "help",
    "safety",
    "medical",
    "unknown",
}
HISTORY_CHARS = 300  # how much of each earlier message the model is shown

_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": sorted(ALLOWED_KINDS)},
        "location": {"type": ["string", "null"]},
        "meal": {"type": ["string", "null"], "enum": [*intents.MEAL_WORDS, None]},
        "tomorrow": {"type": "boolean"},
        "diets": {"type": "array", "items": {"enum": list(intents.DIET_WORDS)}},
        "avoid": {"type": "array", "items": {"enum": list(intents.ALLERGEN_WORDS)}},
        "min_protein_g": {"type": ["number", "null"]},
        "max_calories": {"type": ["number", "null"]},
    },
    "required": ["kind", "location", "meal", "tomorrow", "diets", "avoid"],
}

_UNDERSTAND_PROMPT = """You read messages from NC State students to a dining assistant \
and turn each into JSON. You never answer the question.

kind is one of:
- food: asks what to eat, a menu, or dishes (also with diets, allergies, or calorie/protein goals)
- status: asks if a place is open, or when it opens or closes
- crowd: asks how busy a place is
- locations: asks how many dining places there are, or to list them
- recommend: asks which place to go to, or says they are hungry, without naming a place
- nearby: asks which place is closest, or how far a place is
- help: greets, thanks, or asks what you can do
- safety: asks whether a food is safe
- medical: asks for medical advice
- unknown: anything else

location: a dining place the message names, copied from this list, or null. \
Use null if the message does not name one. Known places: {places}
meal: breakfast, brunch, lunch, dinner, late night, or null.
tomorrow: true only if the message says tomorrow.
diets: any of halal, vegan, vegetarian that the message requires.
avoid: any of dairy, egg, gluten, nuts, pork, seafood, sesame, soy the message avoids.
min_protein_g and max_calories: numbers only if the message gives them."""


class OllamaClient:
    """Talks to an Ollama server's /api/chat. Raises OSError or ValueError on trouble."""

    def __init__(self, url: str, model: str, timeout: float):
        if not url.startswith(("http://", "https://")):
            raise ValueError("the Ollama URL must start with http:// or https://")
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict], schema: dict | None = None) -> str:
        """Send chat messages and return the model's reply text.

        `schema` asks Ollama to answer with JSON in that shape. Temperature is 0 so
        the same message gets the same reading.
        """
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0},
        }
        if schema is not None:
            body["format"] = schema
        request = urllib.request.Request(
            f"{self.url}/api/chat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        # Talk to the server directly, never through a system proxy: Ollama runs on
        # this machine, and looking up proxy settings is slow on macOS.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=self.timeout) as response:
            payload = json.load(response)
        return payload["message"]["content"]


def default_client() -> OllamaClient | None:
    """The model client from the settings, or None while the layer is switched off."""
    if not settings.llm_enabled():
        return None
    return OllamaClient(
        settings.llm_url(), settings.llm_model(), settings.llm_timeout()
    )


def _text(value) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _number(value, maximum: float) -> float | None:
    """A goal the model gave, if it is a plain number in the range the API accepts."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value) if 0 <= value <= maximum else None


def _keys(value, allowed) -> frozenset[str]:
    """The entries of a list that are known keys; anything else is dropped."""
    if not isinstance(value, list):
        return frozenset()
    return frozenset(v for v in value if isinstance(v, str) and v in allowed)


def intent_from_model(data) -> intents.Intent | None:
    """The model's JSON as an Intent, or None if it isn't something we'd accept.

    Nothing is taken on trust: the kind must be a known one, diets and allergens
    must be known keys, and goals must be numbers in range.
    """
    if not isinstance(data, dict):
        return None
    kind = data.get("kind")
    if not isinstance(kind, str) or kind not in ALLOWED_KINDS:
        return None
    meal = data.get("meal")
    return intents.Intent(
        kind=kind,
        location_text=_text(data.get("location")),
        meal=meal if meal in intents.MEAL_WORDS else None,
        day_offset=1 if data.get("tomorrow") is True else 0,
        diets=_keys(data.get("diets"), intents.DIET_WORDS),
        avoid=_keys(data.get("avoid"), intents.ALLERGEN_WORDS),
        min_protein_g=_number(data.get("min_protein_g"), 1000),
        max_calories=_number(data.get("max_calories"), 10000),
    )


def _grounded(
    intent: intents.Intent, texts: list[str], place_names: list[str]
) -> intents.Intent:
    """Keep the model's location only if the student actually mentioned it.

    A small model will pick a place from the list that nobody asked about. The
    rules read the student's own words (this message and their earlier ones) for a
    place; the model's choice survives only if it matches one of those.
    """
    if intent.location_text is None:
        return intent
    wanted = intent.location_text.casefold()
    for text in texts:
        found = intents.parse(text, place_names).location_text
        if found and (wanted in found.casefold() or found.casefold() in wanted):
            return intent
    return replace(intent, location_text=None)


def _context(history: list[dict]) -> list[dict]:
    """Earlier messages as chat turns, each cut short."""
    return [
        {"role": message["role"], "content": message["text"][:HISTORY_CHARS]}
        for message in history
        if message["role"] in ("user", "assistant")
    ]


def understand(
    client, text: str, history: list[dict], place_names: list[str]
) -> intents.Intent | None:
    """Read a message the rules couldn't, or None if the model can't help."""
    system = _UNDERSTAND_PROMPT.format(places=", ".join(place_names) or "none")
    messages = [
        {"role": "system", "content": system},
        *_context(history),
        {"role": "user", "content": text},
    ]
    try:
        intent = intent_from_model(json.loads(client.chat(messages, _SCHEMA)))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if intent is None:
        return None
    spoken = [text, *(m["text"] for m in history if m["role"] == "user")]
    return _grounded(intent, spoken, place_names)

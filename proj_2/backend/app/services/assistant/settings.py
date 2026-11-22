"""Settings for the dining assistant, read from the environment (see .env.example).

The limits are read once when the app starts. Whether the assistant is on is read
on every request, so it can be switched off without a restart in tests.
"""

import os

RATE_PER_MINUTE = int(os.getenv("ASSISTANT_RATE_PER_MINUTE", "10"))  # per account
MAX_MESSAGE_CHARS = int(os.getenv("ASSISTANT_MAX_MESSAGE_CHARS", "500"))
HISTORY_LIMIT = int(os.getenv("ASSISTANT_HISTORY_LIMIT", "200"))  # messages kept
MODEL_HISTORY_MESSAGES = 6  # how many recent messages the language model is shown


def enabled() -> bool:
    """Whether the assistant is switched on (ASSISTANT_ENABLED, on unless "false")."""
    return os.getenv("ASSISTANT_ENABLED", "true").lower() != "false"


# The optional language model (a local Ollama server). On unless "false"; with no
# Ollama running the assistant quietly uses its rules instead.
def llm_enabled() -> bool:
    """Whether the language model layer is on (ASSISTANT_LLM_ENABLED, on unless "false")."""
    return os.getenv("ASSISTANT_LLM_ENABLED", "true").lower() != "false"


def llm_url() -> str:
    """Where Ollama listens (ASSISTANT_LLM_URL, default the local server)."""
    return (os.getenv("ASSISTANT_LLM_URL") or "http://localhost:11434").rstrip("/")


def llm_model() -> str:
    """Which Ollama model to ask (ASSISTANT_LLM_MODEL; blank means qwen2.5:1.5b)."""
    return os.getenv("ASSISTANT_LLM_MODEL") or "qwen2.5:1.5b"


def llm_timeout() -> float:
    """Seconds to wait for the model before using the rule-based answer instead."""
    return float(os.getenv("ASSISTANT_LLM_TIMEOUT_SECONDS") or "30")


# Looking up a typed place that isn't in campus_places.json (OpenStreetMap's
# Nominatim). On unless "false"; offline, the assistant asks where the student is.
def geocode_enabled() -> bool:
    """Whether typed places may be looked up online (ASSISTANT_GEOCODE_ENABLED, on unless "false")."""
    return os.getenv("ASSISTANT_GEOCODE_ENABLED", "true").lower() != "false"


def geocode_url() -> str:
    """The search service (ASSISTANT_GEOCODE_URL, default OpenStreetMap's Nominatim)."""
    return (
        os.getenv("ASSISTANT_GEOCODE_URL") or "https://nominatim.openstreetmap.org"
    ).rstrip("/")


def geocode_timeout() -> float:
    """Seconds to wait for the lookup before asking the student where they are."""
    return float(os.getenv("ASSISTANT_GEOCODE_TIMEOUT_SECONDS") or "5")


# Driving distances for a place too far to walk from (the public OSRM server, free,
# no key). On unless "false"; offline, straight-line miles are shown instead.
def routing_enabled() -> bool:
    """Whether driving distances may be looked up online (ASSISTANT_ROUTING_ENABLED, on unless "false")."""
    return os.getenv("ASSISTANT_ROUTING_ENABLED", "true").lower() != "false"


def routing_url() -> str:
    """The routing service (ASSISTANT_ROUTING_URL, default the public OSRM server)."""
    return (
        os.getenv("ASSISTANT_ROUTING_URL") or "https://router.project-osrm.org"
    ).rstrip("/")


def routing_timeout() -> float:
    """Seconds to wait for a route before showing straight-line distances instead."""
    return float(os.getenv("ASSISTANT_ROUTING_TIMEOUT_SECONDS") or "8")

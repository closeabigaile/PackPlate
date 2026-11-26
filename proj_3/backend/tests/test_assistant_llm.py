"""Tests for the optional language model layer (M3). No real model is ever called:
a stand-in answers, or a tiny local HTTP server plays the part of Ollama.

The model only reads questions. Nothing it writes is ever shown to the student."""

import json
import socketserver
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from app.services.assistant import chat, llm, settings
from app.services.hours import campus_time

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))
PLACES = ["Fountain Dining Hall", "Case Dining Hall"]


class FakeModel:
    """Stands in for the model: returns the given replies in order, or raises one."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def chat(self, messages, schema=None):
        self.calls.append({"messages": messages, "schema": schema})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def reading(**fields):
    """What the model returns when it reads a message: a JSON object of fields."""
    base = {"kind": "food", "location": None, "meal": None, "tomorrow": False}
    return json.dumps({**base, "diets": [], "avoid": [], **fields})


def fountain(seed):
    """Fountain with a dinner menu: rice fits a dairy-free profile, mac and cheese doesn't."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.nutrition("1|rice|1 cup", location_id=1, serving_size="1 cup", calories=200.0)
    seed.nutrition("1|mac|1 cup", location_id=1, serving_size="1 cup", calories=400.0)
    seed.item(11, "Steamed Rice", nutrition_key="1|rice|1 cup")
    seed.item(11, "Mac and Cheese", nutrition_key="1|mac|1 cup", allergens=["dairy"])


def ask(db, text, model, history=None):
    return chat.respond(db, text, None, NOON, history, model)


# --- reading the model's answer -------------------------------------------------


def test_a_good_reading_becomes_an_intent():
    """Valid JSON from the model becomes the same Intent the rules produce."""
    intent = llm.intent_from_model(
        json.loads(
            reading(
                location="Fountain",
                meal="dinner",
                tomorrow=True,
                diets=["vegan"],
                avoid=["dairy"],
                min_protein_g=30,
            )
        )
    )

    assert intent.kind == "food"
    assert (intent.location_text, intent.meal, intent.day_offset) == (
        "Fountain",
        "dinner",
        1,
    )
    assert intent.diets == {"vegan"} and intent.avoid == {"dairy"}
    assert intent.min_protein_g == 30.0


@pytest.mark.parametrize(
    "data",
    [None, "food", {"kind": "order_pizza"}, {}, {"kind": ["food"]}],
)
def test_an_unusable_reading_is_rejected(data):
    """Anything that isn't a known kind of question is thrown away."""
    assert llm.intent_from_model(data) is None


def test_unknown_diets_allergens_and_bad_numbers_are_dropped():
    """The model can't invent a diet, an allergen, or an out-of-range goal."""
    intent = llm.intent_from_model(
        {
            "kind": "food",
            "diets": ["vegan", "carnivore", 7],
            "avoid": ["dairy", "kryptonite", ["x"]],
            "meal": "elevenses",
            "min_protein_g": -5,
            "max_calories": 999999,
        }
    )

    assert intent.diets == {"vegan"}
    assert intent.avoid == {"dairy"}
    assert intent.meal is None
    assert intent.min_protein_g is None and intent.max_calories is None


# --- a place the model names must be one the student mentioned -------------------


def test_a_place_the_student_never_mentioned_is_dropped():
    """The model picked Case from the list although the message names no place."""
    model = FakeModel(reading(location="Case Dining Hall"))

    intent = llm.understand(model, "what do you have with chicken", [], PLACES)

    assert intent.kind == "food"
    assert intent.location_text is None


def test_a_place_the_student_did_mention_is_kept():
    """A place named in this message, or in the student's earlier ones, is kept."""
    now = llm.understand(
        FakeModel(reading(location="Fountain Dining Hall")),
        "anything vegan at fountain?",
        [],
        PLACES,
    )
    earlier = llm.understand(
        FakeModel(reading(location="Case Dining Hall")),
        "and for dessert?",
        [{"role": "user", "text": "what's for dinner at Case"}],
        PLACES,
    )

    assert now.location_text == "Fountain Dining Hall"
    assert earlier.location_text == "Case Dining Hall"


def test_the_model_cannot_send_you_to_a_place_you_did_not_ask_about(db, seed):
    """End to end: a made-up place from the model never reaches the menu lookup."""
    fountain(seed)
    model = FakeModel(reading(location="Fountain Dining Hall"))

    answer = ask(db, "what do you have with chicken", model)

    assert answer["reply"].startswith("Which dining location?")


# --- understanding messages the rules can't -------------------------------------


def test_the_model_reads_a_message_the_rules_cannot(db, seed):
    """A message with no rule keywords is read by the model, and the facts still come from the database."""
    fountain(seed)
    model = FakeModel(
        reading(location="Fountain Dining Hall", meal="dinner", avoid=["dairy"])
    )

    answer = ask(db, "yo fountain hit me with a plate", model)

    assert answer["source"] == "llm"
    assert answer["reply"].startswith("1 item at Fountain Dining Hall")
    assert "- Steamed Rice (200 cal)" in answer["reply"]
    assert "Mac and Cheese" not in answer["reply"]


def test_the_model_sees_the_recent_conversation_and_the_places(db, seed):
    """The model is shown the known places and earlier messages, and asked for JSON."""
    fountain(seed)
    model = FakeModel(reading(kind="help"))
    history = [
        {"role": "user", "text": "what's for dinner at Fountain?"},
        {"role": "assistant", "text": "Here's what's on at Fountain Dining Hall"},
    ]

    ask(db, "ok cool", model, history)

    sent = model.calls[0]["messages"]
    assert sent[0]["role"] == "system" and "Fountain Dining Hall" in sent[0]["content"]
    assert [m["content"] for m in sent[1:]] == [
        "what's for dinner at Fountain?",
        "Here's what's on at Fountain Dining Hall",
        "ok cool",
    ]
    assert model.calls[0]["schema"] is not None


def test_the_rules_come_first_and_the_model_is_not_asked(db, seed):
    """A message the rules understand never reaches the model."""
    fountain(seed)
    model = FakeModel()

    answer = ask(db, "dairy-free options at Fountain tonight", model)

    assert model.calls == []
    assert answer["source"] == "rules"
    assert "Steamed Rice" in answer["reply"]


def test_medical_and_safety_questions_never_reach_the_model(db, seed):
    """The fixed declines come from the rules, whatever the model might say."""
    fountain(seed)
    model = FakeModel()

    medical = ask(db, "what medication for a reaction?", model)
    safety = ask(db, "is the mac and cheese safe for me?", model)

    assert model.calls == []
    assert "can't give medical advice" in medical["reply"]
    assert "can't tell you a dish is safe" in safety["reply"]


def test_a_model_that_says_medical_gets_the_fixed_decline(db, seed):
    """If the model itself classifies a message as medical, it still gets the fixed reply."""
    model = FakeModel(reading(kind="medical"))

    answer = ask(db, "my throat feels itchy and swollen", model)

    assert "can't give medical advice" in answer["reply"]


def test_a_broken_model_falls_back_to_the_rules(db, seed):
    """Garbage, an error, or a timeout from the model leaves the rule-based answer."""
    fountain(seed)
    for failure in ("not json", TimeoutError("slow"), reading(kind="order_pizza")):
        answer = ask(db, "yo hit me with a plate", FakeModel(failure))

        assert answer["source"] == "rules"
        assert "didn't understand" in answer["reply"]


def test_no_model_means_the_rules_alone(db, seed):
    """With the layer switched off the assistant works exactly as before."""
    fountain(seed)

    answer = chat.respond(db, "yo hit me with a plate", None, NOON)

    assert answer["source"] == "rules"
    assert "didn't understand" in answer["reply"]


# --- the Ollama client ----------------------------------------------------------


def test_ollama_is_on_unless_switched_off(monkeypatch):
    """Off means no client; otherwise (unset or "true") it uses the configured URL and model."""
    monkeypatch.setenv("ASSISTANT_LLM_ENABLED", "false")
    assert llm.default_client() is None

    monkeypatch.delenv("ASSISTANT_LLM_ENABLED", raising=False)
    monkeypatch.setenv("ASSISTANT_LLM_MODEL", "")
    client = llm.default_client()

    assert client.url == settings.llm_url()
    assert client.model == "qwen2.5:1.5b"  # a blank setting means the default


def test_the_client_refuses_a_url_that_is_not_http():
    """A file:// or other URL in the settings is rejected."""
    with pytest.raises(ValueError):
        llm.OllamaClient("file:///etc/passwd", "m", 5)


def test_the_client_talks_to_an_ollama_server():
    """It posts the chat to /api/chat with the model and schema, and returns the message text."""
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["body"] = json.loads(
                self.rfile.read(int(self.headers["Content-Length"]))
            )
            reply = json.dumps({"message": {"role": "assistant", "content": "hello"}})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(reply.encode())

        def log_message(self, *args):
            pass

    class QuietServer(HTTPServer):
        def server_bind(self):
            # HTTPServer looks up its own hostname here, which can take 30+ seconds
            # on some networks. The test doesn't need the name.
            socketserver.TCPServer.server_bind(self)
            self.server_name, self.server_port = self.server_address[:2]

    server = QuietServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        client = llm.OllamaClient(f"http://127.0.0.1:{server.server_port}", "tiny", 5)
        text = client.chat([{"role": "user", "content": "hi"}], {"type": "object"})
    finally:
        server.shutdown()
        server.server_close()

    assert text == "hello"
    assert seen["path"] == "/api/chat"
    assert seen["body"]["model"] == "tiny"
    assert seen["body"]["stream"] is False
    assert seen["body"]["format"] == {"type": "object"}
    assert seen["body"]["options"] == {"temperature": 0}


def test_an_unreachable_server_is_an_error_the_layer_absorbs():
    """No server listening: chat() raises OSError, and understand() turns that into None."""
    client = llm.OllamaClient("http://127.0.0.1:9", "tiny", 1)

    with pytest.raises(OSError):
        client.chat([{"role": "user", "content": "hi"}])
    assert llm.understand(client, "hello there", [], []) is None

"""Answer one message (M3): parse it, run the matching tool, word the result.

The saved profile always applies. Restrictions typed in the message are added to
it for this question only, and a message can only make the filter stricter: it
can never remove a saved restriction or loosen a limit.

Every reply built from a tool result is checked by validate.py before it is
returned. A reply that fails the check is replaced by a plain fallback.

The language model (llm.py) is optional. It only reads messages the rules can't;
every word of the reply still comes from answers.py and every fact from tools.py.
"""

import re
from dataclasses import replace
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories import location_points as points_repo
from app.repositories import locations as locations_repo
from app.services import filter_engine
from app.services.assistant import (
    answers,
    geocode,
    intents,
    llm,
    places,
    routing,
    tools,
    validate,
)
from app.services.hours import campus_time
from db import seed_location_points

# Questions that are about one place, and so can borrow it from an earlier message.
_ABOUT_A_PLACE = {"food", "crowd"}
_TOPICS = {"food", "status", "crowd"}


def _stricter(a: float | None, b: float | None, pick) -> float | None:
    """The stricter of two optional limits: max() for a minimum, min() for a maximum. None means no limit."""
    values = [v for v in (a, b) if v is not None]
    return pick(values) if values else None


def merge_profile(
    saved: filter_engine.Profile, intent: intents.Intent
) -> filter_engine.Profile:
    """The saved profile plus what the message asked for. Never looser than saved."""
    return filter_engine.Profile(
        avoid=saved.avoid | intent.avoid,
        diets=saved.diets | intent.diets,
        min_protein_g=_stricter(saved.min_protein_g, intent.min_protein_g, max),
        max_calories=_stricter(saved.max_calories, intent.max_calories, min),
        max_sodium_mg=saved.max_sodium_mg,
    )


def _restricted(profile: filter_engine.Profile) -> bool:
    """Whether the profile has any restriction or goal, so the menu must be filtered."""
    return bool(
        profile.avoid
        or profile.diets
        or profile.min_protein_g is not None
        or profile.max_calories is not None
        or profile.max_sodium_mg is not None
    )


def _carry_over(
    intent: intents.Intent, history: list[dict], names: list[str]
) -> intents.Intent:
    """Fill in what a short follow-up leaves out, from the student's earlier messages.

    "and tomorrow?" after a question about Fountain's dinner means Fountain's dinner
    tomorrow. "What about vegan options?" keeps the place from before. This reads
    the student's own words with the same rules as everything else, so it needs no
    language model. It only ever adds a place, meal, or restriction the student
    mentioned earlier; it never removes anything.
    """
    earlier = [
        intents.parse(m["text"], names)
        for m in reversed(history)
        if m["role"] == "user"
    ]
    topic = next((p for p in earlier if p.kind in _TOPICS), None)
    # Only a place asked about for food, hours or crowds is worth borrowing. In a
    # distance question the "place" is where the student is, not a dining location.
    place = next(
        (p.location_text for p in earlier if p.location_text and p.kind in _TOPICS),
        None,
    )

    if intent.kind == "unknown":
        # Only a time, a meal, a diet, or a place: a follow-up, not a question.
        says_something = bool(
            intent.day_offset
            or intent.meal
            or intent.diets
            or intent.avoid
            or intent.min_protein_g is not None
            or intent.max_calories is not None
            or intent.location_text
        )
        if topic is None or not says_something:
            return intent
        return replace(
            intent,
            kind=topic.kind,
            location_text=intent.location_text or topic.location_text,
            meal=intent.meal or topic.meal,
            diets=intent.diets or topic.diets,
            avoid=intent.avoid or topic.avoid,
            min_protein_g=(
                intent.min_protein_g
                if intent.min_protein_g is not None
                else topic.min_protein_g
            ),
            max_calories=(
                intent.max_calories
                if intent.max_calories is not None
                else topic.max_calories
            ),
        )
    if intent.kind in _ABOUT_A_PLACE and not intent.location_text and place:
        return replace(intent, location_text=place)
    return intent


def _reply(text: str, cards: list[dict] | None = None, source: str = "rules") -> dict:
    """Package a reply: its text, the result cards to show with it, and where it came from."""
    return {"reply": text, "cards": cards or [], "source": source}


def _checked(
    text: str,
    cards: list[dict],
    result,
    *,
    locations: list[str],
    all_locations: list[str],
    warning: bool = False,
    source: str = "rules",
) -> dict:
    """The reply, if it matches the tool result it was built from; otherwise the fallback.

    A fallback reply carries `problems`, the reasons the check failed, for debugging.
    """
    found = validate.problems(
        text,
        result,
        allowed_locations=locations,
        all_locations=all_locations,
        require_warning=warning,
    )
    if found:
        return {
            "reply": answers.fallback(),
            "cards": [],
            "source": "fallback",
            "problems": found,
        }
    return _reply(text, cards, source)


def _asked_where_i_am(history: list[dict]) -> bool:
    """Whether the assistant's last reply asked the student where they are."""
    last = next((m for m in reversed(history) if m["role"] == "assistant"), None)
    return bool(last and last["text"].startswith("Where are you?"))


def _nearby(
    db, text, profile, intent, at, all_names, source, place, finder, asked_where, roads
) -> dict:
    """The answer to a distance question, or a request to say where the student is.

    The place comes from campus_places.json if it is listed there; otherwise the
    phrase the student typed is looked up online (if that is switched on).
    """
    seed_location_points.ensure(db)  # fill in any known position that is missing
    if not points_repo.points(db):
        return _reply(answers.nearby_not_ready(place), source=source)
    found = places.find_spot(text)
    asked_for_lookup = False
    if found is None and finder is not None:
        phrase = intents.where_phrase(text) or (text.strip() if asked_where else None)
        if phrase:
            asked_for_lookup = True
            found = finder.lookup(phrase)
    if found is None:
        ask = answers.ask_origin(places.spot_names())
        if asked_for_lookup:
            ask = f"{answers.place_not_found()} {ask}"
        return _reply(ask, source=source)
    name, point = found
    result = tools.nearest(db, name, point, profile, at, intent.meal, roads)
    return _checked(
        answers.nearby(result),
        [],
        result,
        locations=[pick["name"] for pick in result["picks"]],
        all_locations=all_names,
        warning=result["filtered"] and bool(result["picks"]),
        source=source,
    )


def respond(
    db: Session,
    text: str,
    profile: filter_engine.Profile | None = None,
    at: datetime | None = None,
    history: list[dict] | None = None,
    model=None,
    geocoder=None,
    router=None,
) -> dict:
    """The assistant's answer to `text`: {"reply", "cards", "source"}.

    `history` is the recent conversation as [{"role", "text"}], oldest first, so a
    follow-up like "what about tomorrow?" can be understood. `model` is a language
    model client; by default the one from the settings (None while switched off).
    `source` is "rules", "llm" when the model read the question, or "fallback".
    `geocoder` finds a typed place that campus_places.json doesn't list, and
    `router` gives driving distances from a place too far to walk; by default the
    ones from the settings (None while switched off).
    """
    saved = profile or filter_engine.Profile()
    at = campus_time(at)
    history = history or []
    listed = locations_repo.list_locations(db)
    all_names = [loc.name for loc in listed]
    place = all_names[0] if all_names else None  # a real name for example questions
    client = model if model is not None else llm.default_client()
    finder = geocoder if geocoder is not None else geocode.default()
    roads = router if router is not None else routing.default()
    intent = _carry_over(intents.parse(text, all_names), history, all_names)

    # A reply to "Where are you?" is the place, whatever it looks like.
    asked_where = _asked_where_i_am(history)
    if intent.kind == "unknown" and asked_where and (places.find_spot(text) or finder):
        intent = replace(intent, kind="nearby")

    # The rules came up empty: ask the model to read it, if there is one.
    source = "rules"
    if intent.kind == "unknown" and client is not None:
        guessed = llm.understand(client, text, history, all_names)
        if guessed is not None and guessed.kind != "unknown":
            intent, source = _carry_over(guessed, history, all_names), "llm"

    # Questions that need no data get their fixed replies first.
    if intent.kind == "medical":
        return _reply(answers.medical(), source=source)
    if intent.kind == "safety":
        return _reply(answers.safety(place), source=source)
    if intent.kind == "help":
        return _reply(answers.examples(place), source=source)
    if intent.kind == "unknown":
        return _reply(answers.not_understood(place))

    effective = merge_profile(saved, intent)

    # "Which dining hall is near Talley?" ranks the locations by walking distance
    # from a campus place the student named.
    if intent.kind == "nearby":
        return _nearby(
            db,
            text,
            effective,
            intent,
            at,
            all_names,
            source,
            place,
            finder,
            asked_where,
            roads,
        )

    # "How many dining halls are there?" lists the locations that have menus.
    if intent.kind == "locations":
        result = tools.list_locations(db)
        return _checked(
            answers.locations_list(result),
            [],
            result,
            locations=all_names,
            all_locations=all_names,
            source=source,
        )

    # "Which hall do you recommend?" ranks the places that are open now.
    if intent.kind == "recommend":
        result = tools.recommend(db, effective, at, intent.meal)
        return _checked(
            answers.recommend(result),
            [],
            result,
            locations=[pick["name"] for pick in result["picks"]],
            all_locations=all_names,
            warning=bool(result["picks"]),
            source=source,
        )

    # "Which halls are open today?" lists each place's hours for that day.
    day_word = "tomorrow" if intent.day_offset else "today"
    asks_for_a_day = intent.day_offset or re.search(r"\btoday\b", text.casefold())
    if (
        intent.kind == "status"
        and not intent.location_text
        and asks_for_a_day
        and not re.search(r"\bnow\b", text.casefold())
    ):
        day = at.date() + timedelta(days=intent.day_offset)
        open_rows, closed, unknown = [], 0, 0
        for loc in listed:
            hours = tools.get_hours(db, loc.id, day)
            if hours["status"] == "open":
                open_rows.append((loc.name, hours["periods"]))
            elif hours["status"] == "closed":
                closed += 1
            else:
                unknown += 1
        return _checked(
            answers.open_day(day_word, open_rows, closed, unknown),
            [],
            {"open": open_rows, "closed": closed, "unknown": unknown},
            locations=[name for name, _ in open_rows],
            all_locations=all_names,
            source=source,
        )

    # "What's open right now?" names no location: check every location's hours.
    if intent.kind == "status" and not intent.location_text:
        rows, unknown = [], 0
        for loc in listed:
            status = tools.get_status(db, loc.id, at)
            if status["is_open"] is True:
                rows.append((loc.name, status["closes_at"]))
            elif status["is_open"] is None:
                unknown += 1
        return _checked(
            answers.open_now(rows, unknown),
            [],
            {"open": rows, "unknown": unknown},
            locations=[name for name, _ in rows],
            all_locations=all_names,
            source=source,
        )

    # Every other question needs one location: ask, or stop if the name is unclear.
    if not intent.location_text:
        return _reply(answers.ask_location(place), source=source)
    found = tools.find_location(db, intent.location_text)
    if found["candidates"]:
        return _reply(answers.ask_which(found["candidates"]), source=source)
    if found["match"] is None:
        return _reply(answers.unknown_location(intent.location_text), source=source)
    location = found["match"]
    named = {
        "locations": [location["name"]],
        "all_locations": all_names,
        "source": source,
    }

    if intent.kind == "status":
        status = tools.get_status(db, location["id"], at)
        return _checked(
            answers.status_one(location["name"], status), [], status, **named
        )
    if intent.kind == "crowd":
        crowd = tools.get_crowd(db, location["id"], at)
        return _checked(answers.crowd(location["name"], crowd), [], crowd, **named)

    # A food question: filter the menu if there is anything to filter by, otherwise
    # show it plainly.
    day = at.date() + timedelta(days=intent.day_offset)
    when = "tomorrow" if intent.day_offset else "today"
    if _restricted(effective):
        result = tools.filter_items(db, location["id"], day, effective, intent.meal)
        reply, cards = answers.food_filtered(
            location["name"], result, when, intent.meal
        )
    else:
        result = tools.get_menu(db, location["id"], day, intent.meal)
        reply, cards = answers.food_menu(location["name"], result, when, intent.meal)
    # The label warning goes with any reply that lists food, not with "no menu yet".
    lists_food = bool(result.get("items_checked") or result.get("menus"))
    return _checked(reply, cards, result, warning=lists_food, **named)

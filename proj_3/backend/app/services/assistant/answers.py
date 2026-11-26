"""Reply wording for the dining assistant (M3).

Every function here turns a tool result into text. The words are fixed; the
facts are filled in from the result and nothing else, so a reply can't state a
dish, number, or time a tool didn't return. Dietary answers say "fits your
filters", never "safe".
"""

from datetime import datetime

from app.services.crowd import WINDOW

MAX_SHOWN = 5  # items listed in a filtered reply
MENU_NAMES_SHOWN = 8  # dish names listed per meal in an unfiltered menu reply
LABEL_WARNING = "Labels can be wrong; check ingredients."

# {place} is filled with a real location name from the database (see place_for).
EXAMPLES = (
    "What's for dinner at {place} tonight?",
    "Vegan, high-protein options at {place}",
    "Dairy-free lunch under 600 calories at {place}",
    "What's open right now?",
    "When does {place} close tonight?",
    "Is {place} busy right now?",
    "How many dining halls are there?",
    "Which dining hall is near Talley Student Union?",
)

CROWD_WORDS = {
    "not_busy": "not busy",
    "moderate": "moderately busy",
    "crowded": "crowded",
}


def _clock(iso: str) -> str:
    """A stored time as a clock time for a reply: "2026-10-06T21:00:00-04:00" becomes "9:00 pm"."""
    return datetime.fromisoformat(iso).strftime("%I:%M %p").lstrip("0").lower()


clock = (
    _clock  # the public name, used by validate.py to know which times a reply may show
)


def _plural(n: int, word: str) -> str:
    """A count with its noun: "1 item", "3 items"."""
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _numbers(item: dict) -> str:
    """An item's calories and protein as " (200 cal, 4 g protein)", leaving out any that are unknown."""
    parts = []
    if item["calories"] is not None:
        parts.append(f"{item['calories']:g} cal")
    if item["protein_g"] is not None:
        parts.append(f"{item['protein_g']:g} g protein")
    return f" ({', '.join(parts)})" if parts else ""


def example_questions(place: str | None = None) -> list[str]:
    """The example questions, naming `place` (a real location).

    With no known location, only the questions that don't need one are returned,
    so every example shown is one the assistant can actually answer.
    """
    if place is None:
        return [q for q in EXAMPLES if "{place}" not in q]
    return [q.format(place=place) for q in EXAMPLES]


def examples(place: str | None = None) -> str:
    """The reply to "help": what the assistant can do, with example questions."""
    lines = "\n".join(f"- {q}" for q in example_questions(place))
    return f"I can help with menus, dietary filters, hours, and crowds. Try:\n{lines}"


def not_understood(place: str | None = None) -> str:
    """The reply when a message matches no known question: say so, then show examples."""
    return "I didn't understand that. " + examples(place)


def fallback() -> str:
    """The reply when a built answer fails validation: say so rather than show it."""
    return (
        "I couldn't put together a reliable answer to that. "
        "Please try asking another way."
    )


def medical() -> str:
    """The fixed reply to a medical question: decline and point to a professional."""
    return (
        "I can't give medical advice. For allergy or health questions, "
        "ask a doctor or dietitian."
    )


def safety(place: str | None = None) -> str:
    """The fixed reply to "is this safe?": the assistant never says a dish is safe, only what fits."""
    questions = example_questions(place)
    # The second example is the filtered one; without a location only one remains.
    hint = questions[1] if place else questions[0]
    return (
        "I can't tell you a dish is safe. I can show which dishes fit your "
        f"filters, but labels can be wrong, so check the ingredients. Try: "
        f'"{hint}".'
    )


def nearby_not_ready(place: str | None = None) -> str:
    """The reply to "which hall is closest?" when no coordinates are loaded at all."""
    hint = example_questions(place)[0]
    return (
        "I can't tell which dining hall is closest, because I don't have "
        "locations for the dining halls loaded. I can show what's "
        f'open right now, or recommend a place that fits your diet. Try: "{hint}".'
    )


def place_not_found() -> str:
    """The start of the reply when a typed place couldn't be found near campus."""
    return "I couldn't find that place near campus."


def ask_origin(spots: list[str]) -> str:
    """The reply when the student asks what is near them but names no known place."""
    names = ", ".join(spots[:3])
    return (
        "Where are you? Type a campus place, like a dorm or a building, and I'll "
        f"find the dining locations closest to it (for example {names})."
    )


def nearby(result: dict) -> str:
    """The reply to "which dining hall is near <place>?": the closest, with rough walks.

    Each line gives the facts the ranking used: the walking estimate, whether it is
    open (and until when), and how many items fit the diet if one is saved.
    """
    picks = result["picks"]
    if not picks:
        return (
            f"I don't have locations for any dining place near {result['origin']} yet."
        )
    lines = [f"Closest to {result['origin']}:"]
    for pick in picks:
        if result.get("driving"):
            walk = (
                f"about {pick['drive_miles']:g} mi, "
                f"{pick['drive_minutes']} min by car"
            )
        elif result.get("far"):
            walk = f"about {pick['miles']:g} mi away in a straight line"
        else:
            walk = f"about {_plural(pick['walk_minutes'], 'min')} walk"
        if pick["is_open"] is True:
            hours = f"open until {_clock(pick['closes_at'])}"
        elif pick["is_open"] is False:
            hours = "closed right now"
        else:
            hours = "hours unknown"
        parts = [walk, hours]
        if result["filtered"]:
            n = pick["fits"]
            parts.append(
                f"{_plural(n, 'item')} {'fits' if n == 1 else 'fit'} your filters"
            )
        lines.append(f"- {pick['name']} ({'; '.join(parts)})")
    if result.get("driving"):
        lines.append(
            "That's too far to walk. Driving distances and times are estimates "
            "for light traffic; a real trip can take longer."
        )
    elif result.get("far"):
        lines.append(
            "That's too far to walk. These are straight-line distances, so the "
            "trip by road will be longer; I couldn't get driving distances."
        )
    else:
        lines.append("Walking times are rough estimates from straight-line distance.")
    if result["unplaced"]:
        lines.append(
            f"I don't have a location for {_plural(result['unplaced'], 'other place')} yet, "
            "so they aren't ranked."
        )
    if result["filtered"]:
        lines.append(LABEL_WARNING)
    return "\n".join(lines)


def recommend(result: dict) -> str:
    """The reply to "which hall do you recommend?": the best open places and why.

    Each line gives the facts the ranking used: when it closes, how many items fit
    (or are on the menu if no diet is saved), and how busy it is.
    """
    picks = result["picks"]
    if not picks:
        return "Nothing I know of is open right now, so I can't recommend a place."
    lines = ["Here's where I'd go right now:"]
    for pick in picks:
        if result["filtered"]:
            n = pick["fits"]
            food = f"{_plural(n, 'item')} {'fits' if n == 1 else 'fit'} your filters"
        else:
            food = f"{_plural(pick['items_checked'], 'item')} on the menu"
        if pick["crowd"] is None:
            crowd = "no recent crowd reports"
        else:
            reports = _plural(pick["reports"], "report")
            crowd = f"{CROWD_WORDS[pick['crowd']]}, {reports}"
        until = f"open until {_clock(pick['closes_at'])}"
        lines.append(f"- {pick['name']} ({until}; {food}; {crowd})")
    lines.append(LABEL_WARNING)
    return "\n".join(lines)


def locations_list(result: dict) -> str:
    """The reply to "how many dining halls are there?": the count and the names."""
    names = [loc["name"] for loc in result["locations"]]
    if not names:
        return "I don't have any dining locations loaded yet."
    lines = [f"I know of {_plural(len(names), 'dining location')} with menus:"]
    lines += [f"- {name}" for name in names]
    return "\n".join(lines)


def unknown_location(text: str) -> str:
    """The reply when a typed location name matches no known location."""
    return f'I don\'t know a location called "{text}".'


def ask_which(candidates: list[dict]) -> str:
    """The reply when a typed name fits several locations: ask which one is meant."""
    names = ", ".join(c["name"] for c in candidates)
    return f"Which location do you mean: {names}?"


def ask_location(place: str | None = None) -> str:
    """The reply when a question needs a location and the message names none."""
    if place:
        return f"Which dining location? For example: {place}."
    return "Which dining location?"


def food_filtered(
    location_name: str, result: dict, when: str, meal: str | None
) -> tuple[str, list[dict]]:
    """The reply and result cards for items checked against a profile."""
    for_meal = f" for {meal}" if meal else ""
    # No items at all means no menu was scraped; say that instead of "nothing fits".
    if result["items_checked"] == 0:
        return f"I don't have a menu for {location_name} {when} yet.", []
    # List the items that fit, up to MAX_SHOWN, and count the rest.
    fits = result["fits"]
    shown = fits[:MAX_SHOWN]
    lines = []
    if fits:
        verb = "fits" if len(fits) == 1 else "fit"
        lines.append(
            f"{_plural(len(fits), 'item')} at {location_name} {when}{for_meal} "
            f"{verb} your filters:"
        )
        lines += [f"- {item['name']}{_numbers(item)}" for item in shown]
        if len(fits) > len(shown):
            lines.append(f"...and {len(fits) - len(shown)} more.")
    else:
        lines.append(f"Nothing at {location_name} {when}{for_meal} fits your filters.")
    # Say how many items conflict, and how many can't be checked at all.
    conflicts = result["conflicts"]
    if conflicts:
        verb = "conflicts" if conflicts == 1 else "conflict"
        lines.append(f"{_plural(conflicts, 'item')} {verb} with your filters.")
    # Items the filter couldn't confirm are never listed as fitting; mention them separately.
    incomplete = result["incomplete"]
    if incomplete:
        first = incomplete[0]
        why = f": {first['reasons'][0]}" if first["reasons"] else ""
        noun = "more item" if fits else "item"
        lines.append(
            f"{_plural(len(incomplete), noun)} can't be confirmed, "
            f"for example {first['name']}{why}."
        )
    lines.append(LABEL_WARNING)
    cards = [{"type": "menu_item", **item} for item in shown]
    return "\n".join(lines), cards


def food_menu(
    location_name: str, result: dict, when: str, meal: str | None
) -> tuple[str, list[dict]]:
    """The reply for a menu that wasn't checked against any restrictions."""
    menus = result["menus"]
    if not menus:
        return f"I don't have a menu for {location_name} {when} yet.", []
    lines = [f"Here's what's on at {location_name} {when}:"]
    for menu in menus:
        if not menu["scraped"]:
            lines.append(f"{menu['meal']}: listed, but the items aren't available yet.")
            continue
        names = [item["name"] for item in menu["items"]]
        hidden = len(names) - MENU_NAMES_SHOWN
        extra = f" (+{hidden} more)" if hidden > 0 else ""
        shown = ", ".join(names[:MENU_NAMES_SHOWN])
        lines.append(f"{menu['meal']}: {shown}{extra}")
    lines.append("I haven't filtered these for your diet.")
    lines.append(LABEL_WARNING)
    return "\n".join(lines), []


def status_one(location_name: str, status: dict) -> str:
    """The reply about one location's hours: open until, closed until, or hours unknown."""
    if status["is_open"] is None:
        return f"I don't have hours for {location_name} today."
    if status["is_open"]:
        return f"{location_name} is open until {_clock(status['closes_at'])}."
    if status["opens_next_at"]:
        return (
            f"{location_name} is closed now. It opens again at "
            f"{_clock(status['opens_next_at'])}."
        )
    return f"{location_name} is closed for the rest of today."


def open_now(rows: list[tuple[str, str]], unknown: int) -> str:
    """rows: (name, closes_at) for locations open now; unknown: locations without hours."""
    if rows:
        lines = ["Open right now:"]
        lines += [f"- {name}, until {_clock(closes)}" for name, closes in rows]
    else:
        lines = ["Nothing I know of is open right now."]
    if unknown:
        lines.append(f"I don't have hours for {_plural(unknown, 'location')}.")
    return "\n".join(lines)


def open_day(
    when: str, rows: list[tuple[str, list[dict]]], closed: int, unknown: int
) -> str:
    """The reply to "which dining halls are open today/tomorrow?": each place with its hours.

    rows: (name, periods) for the locations open that day, each period
    {"opens_at", "closes_at"}; closed: how many are closed all day; unknown: how
    many have no hours stored.
    """
    if rows:
        lines = [f"Open {when}:"]
        for name, periods in rows:
            hours = ", ".join(
                f"{_clock(p['opens_at'])} to {_clock(p['closes_at'])}" for p in periods
            )
            lines.append(f"- {name} ({hours})")
    else:
        lines = [f"Nothing I know of is open {when}."]
    if closed:
        lines.append(f"{_plural(closed, 'place')} closed all day {when}.")
    if unknown:
        lines.append(f"I don't have hours for {_plural(unknown, 'location')} {when}.")
    return "\n".join(lines)


def crowd(location_name: str, result: dict) -> str:
    """The reply about how busy a location is. No recent reports is said as unknown, not "not busy"."""
    if result["level"] is None:
        return (
            f"No recent reports for {location_name}, " "so I can't say how busy it is."
        )
    minutes = int(WINDOW.total_seconds() // 60)
    return (
        f"{location_name} looks {CROWD_WORDS[result['level']]}: "
        f"{_plural(result['report_count'], 'student report')} "
        f"in the last {minutes} minutes."
    )

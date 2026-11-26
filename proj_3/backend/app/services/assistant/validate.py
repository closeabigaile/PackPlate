"""Check a reply against the tool result it was built from (M3).

A reply may state only what a tool returned. This module takes the reply text
and the tool result and lists everything that doesn't match: a number or time
the result doesn't have, a dish or location the result doesn't name, wording
that claims safety, or a missing label warning. An empty list means the reply is
consistent with the result.

The replies are built from fixed templates today, so a problem here means a
bug or a template change. It becomes the main safety check once a language
model is allowed to reword replies.
"""

import re
from datetime import datetime

from app.services.assistant import answers
from app.services.crowd import WINDOW

# Any word that claims safety. Dietary answers say "fits your filters" instead.
BANNED = re.compile(r"\b(safe\w*|guarantee\w*|allergy[- ]free|risk[- ]free)\b", re.I)

_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MENU_LINE = re.compile(r"^(?P<meal>[^:\n]+): (?P<rest>.*)$")
_MORE = re.compile(r" \(\+\d+ more\)$")


def _walk_string(value: str, numbers: set[str], strings: set[str]) -> None:
    """Record a string from a result: a time as the clock time a reply shows, text as itself."""
    if _DATE_ONLY.match(value):
        return
    if "T" in value:
        try:
            datetime.fromisoformat(value)
        except ValueError:
            pass
        else:
            numbers.update(_NUMBER.findall(answers.clock(value)))
            return
    strings.add(value)
    numbers.update(_NUMBER.findall(value))


def _walk(value, numbers: set[str], strings: set[str]) -> None:
    """Collect every number and string in a tool result, skipping database ids."""
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int | float):
        numbers.add(f"{value:g}")
    elif isinstance(value, str):
        _walk_string(value, numbers, strings)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key == "id" or key.endswith("_id"):
                continue
            _walk(item, numbers, strings)
    elif isinstance(value, list | tuple):
        # A reply can state how many items there are, or how many are not shown.
        count = len(value)
        counts = (count, count - answers.MAX_SHOWN, count - answers.MENU_NAMES_SHOWN)
        numbers.update(str(n) for n in counts if n > 0)
        for item in value:
            _walk(item, numbers, strings)


def allowed(result) -> tuple[set[str], set[str]]:
    """The numbers and the text a reply built from `result` is allowed to contain."""
    numbers = {str(int(WINDOW.total_seconds() // 60))}  # "in the last 30 minutes"
    strings: set[str] = set()
    _walk(result, numbers, strings)
    return numbers, strings


def _is_bullet_for(text: str, names: set[str]) -> bool:
    """Whether a "- ..." line starts with a known name, as the reply templates write it."""
    return any(
        text == name or text.startswith((f"{name} (", f"{name}, until"))
        for name in names
    )


def _is_run_of(rest: str, names: list[str]) -> bool:
    """Whether `rest` is known names joined by ", " (a menu line), allowing a "(+N more)" tail."""
    rest = _MORE.sub("", rest)
    longest_first = sorted(names, key=len, reverse=True)
    while rest:
        for name in longest_first:
            if rest == name:
                rest = ""
                break
            if rest.startswith(f"{name}, "):
                rest = rest[len(name) + 2 :]
                break
        else:
            return False
    return True


def _menu_names(result) -> tuple[set[str], list[str]]:
    """The meals and the dish names in a get_menu result; empty for any other result."""
    if not isinstance(result, dict) or "menus" not in result:
        return set(), []
    meals = {menu["meal"] for menu in result["menus"]}
    names = [item["name"] for menu in result["menus"] for item in menu["items"]]
    return meals, names


def problems(
    reply: str,
    result,
    *,
    allowed_locations=(),
    all_locations=(),
    require_warning: bool = False,
) -> list[str]:
    """Everything in `reply` that the tool `result` doesn't support. Empty means it is consistent.

    allowed_locations: location names the reply may mention.
    all_locations: every known location name, so a mix-up with another one is caught.
    require_warning: whether the label warning must be present (food answers).
    """
    found = []

    if banned := BANNED.search(reply):
        found.append(f"uses a banned word: {banned.group(0)!r}")

    numbers, strings = allowed(result)
    for number in _NUMBER.findall(reply):
        if number not in numbers:
            found.append(f"number {number} is not in the tool result")

    # Names a list line may start with: anything the result names, plus the locations.
    names = strings | set(allowed_locations)
    meals, menu_names = _menu_names(result)
    for line in reply.splitlines():
        if line.startswith("- "):
            if not _is_bullet_for(line[2:], names):
                found.append(f"list line {line!r} names nothing from the tool result")
        elif match := _MENU_LINE.match(line):
            if match["meal"] in meals and not match["rest"].startswith("listed, but"):
                if not _is_run_of(match["rest"], menu_names):
                    found.append(f"menu line {line!r} lists a dish not in the result")

    for name in all_locations:
        if name not in allowed_locations and name.casefold() in reply.casefold():
            found.append(f"mentions another location: {name!r}")

    if require_warning and answers.LABEL_WARNING not in reply:
        found.append("is missing the label warning")

    return list(dict.fromkeys(found))

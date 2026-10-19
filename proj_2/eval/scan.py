"""Ingredient scan: does an item's ingredient text name something a profile avoids?

This is M0's independent safety check. PackPlate's filter never reads
ingredient text (it uses the icons and the label's "Contains:" line), so a
`fits` item whose ingredients name an avoided allergen is a lead worth a
human look. The words are in eval/wordlist.py.

Two kinds of hit are kept apart:
- `terms`: words in the ingredients themselves.
- `advisory`: words only inside a cross-contact warning ("may contain",
  "made in a facility that also processes ..."). Those aren't ingredients,
  so they're reported separately, not counted as false fits.
"""

import re
from dataclasses import dataclass, field

from eval.wordlist import WORDS

# Cross-contact warnings run to the end of their sentence.
_ADVISORY = re.compile(
    r"(may contain|in a facility|on shared equipment|on equipment that|"
    r"same equipment|made in a plant)[^.]*",
    re.I,
)
# "gluten-free", "dairy free", "non-dairy": the opposite of an ingredient.
_FREE_OF = re.compile(r"\b[a-z]+[- ]free\b|\bnon-?dairy\b", re.I)


@dataclass
class Hits:
    terms: list[str] = field(default_factory=list)
    advisory: list[str] = field(default_factory=list)


def term_pattern(term: str) -> re.Pattern:
    """Whole words, any case, optional plural; "half and half" also matches hyphens."""
    words = r"[\s-]+".join(re.escape(w) for w in term.split())
    return re.compile(rf"\b{words}(?:e?s)?\b", re.I)


_PATTERNS = {
    key: (
        [(t, term_pattern(t)) for t in spec["terms"]],
        [term_pattern(e) for e in spec["except_"]],
    )
    for key, spec in WORDS.items()
}


def _find(text: str, key: str) -> list[str]:
    terms, exceptions = _PATTERNS[key]
    for e in exceptions:  # before _FREE_OF, so "gluten-free flour" is one phrase
        text = e.sub(" ", text)
    text = _FREE_OF.sub(" ", text)
    return sorted({t for t, p in terms if p.search(text)})


def scan(ingredients: str | None, profile_key: str) -> Hits:
    """Words in `ingredients` that break the profile, split by where they appear."""
    if not ingredients:
        return Hits()
    advisory_text = " ".join(m.group(0) for m in _ADVISORY.finditer(ingredients))
    main_text = _ADVISORY.sub(" ", ingredients)
    terms = _find(main_text, profile_key)
    advisory = [t for t in _find(advisory_text, profile_key) if t not in terms]
    return Hits(terms, advisory)

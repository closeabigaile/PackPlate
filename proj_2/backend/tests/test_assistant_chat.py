"""Tests for answering a message end to end (M3): parse, tool, reply."""

from datetime import date, datetime, timedelta

from app.services import filter_engine
from app.services.assistant import chat
from app.services.hours import campus_time

DAY = date(2026, 10, 6)
NOON = campus_time(datetime(2026, 10, 6, 12, 0))


def fountain(seed):
    """Fountain with a dinner menu: rice fits a dairy-free profile, mac and cheese doesn't."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.nutrition("1|rice|1 cup", location_id=1, serving_size="1 cup", calories=200.0)
    seed.nutrition("1|mac|1 cup", location_id=1, serving_size="1 cup", calories=400.0)
    seed.item(11, "Steamed Rice", nutrition_key="1|rice|1 cup")
    seed.item(11, "Mac and Cheese", nutrition_key="1|mac|1 cup", allergens=["dairy"])
    seed.point(1, 35.78547, -78.67764)


def ask(db, text, profile=None):
    """Send one message to the assistant as if it were noon on the test day."""
    return chat.respond(db, text, profile, NOON)


def test_restrictions_in_the_message_filter_the_menu(db, seed):
    """ "Dairy-free" in the message hides the dairy dish, shows numbers, and adds the label warning."""
    fountain(seed)

    answer = ask(db, "dairy-free options at Fountain tonight")

    assert "Steamed Rice (200 cal)" in answer["reply"]
    assert "Mac and Cheese" not in answer["reply"]
    assert chat.answers.LABEL_WARNING in answer["reply"]
    assert "safe" not in answer["reply"].lower()
    assert [c["name"] for c in answer["cards"]] == ["Steamed Rice"]
    assert answer["source"] == "rules"


def test_a_plain_menu_question_says_it_is_not_filtered(db, seed):
    """With no restrictions anywhere, the whole menu is shown and the reply says it wasn't filtered."""
    fountain(seed)

    reply = ask(db, "what's for dinner at Fountain tonight?")["reply"]

    assert "Steamed Rice" in reply and "Mac and Cheese" in reply
    assert "haven't filtered" in reply


def test_the_saved_profile_applies_without_being_mentioned(db, seed):
    """A saved dairy restriction filters the menu even when the message doesn't mention it."""
    fountain(seed)
    saved = filter_engine.Profile(avoid=frozenset({"dairy"}))

    reply = ask(db, "what's for dinner at Fountain tonight?", saved)["reply"]

    assert "Steamed Rice" in reply
    assert "Mac and Cheese" not in reply


def test_a_message_cannot_loosen_the_saved_profile(db, seed):
    """ "I'm fine with dairy" and a higher calorie limit in the message don't weaken the saved profile."""
    fountain(seed)
    saved = filter_engine.Profile(avoid=frozenset({"dairy"}), max_calories=300.0)

    reply = ask(
        db, "I'm fine with dairy, dinner at Fountain under 900 calories", saved
    )["reply"]

    assert "Mac and Cheese" not in reply
    merged = chat.merge_profile(saved, chat.intents.parse("under 900 calories"))
    assert merged.max_calories == 300.0
    assert merged.avoid == {"dairy"}


def test_items_without_a_label_are_not_called_a_fit(db, seed):
    """A dish with no label is mentioned as "can't be confirmed", never listed as a fit."""
    fountain(seed)
    seed.item(11, "Chef's Special")

    reply = ask(db, "dairy-free dinner at Fountain")["reply"]

    assert "Chef's Special" in reply
    assert "can't be confirmed" in reply
    assert "- Chef's Special" not in reply


def test_hours_for_one_location_and_for_everything(db, seed):
    """ "Is Fountain open?" answers for one location; "what's open?" lists every open location."""
    fountain(seed)
    seed.hours(1, DAY, "open", windows=[(420, 1260)])

    assert "open until 9:00 pm" in ask(db, "is Fountain open?")["reply"]
    assert (
        "Fountain Dining Hall, until 9:00 pm"
        in ask(db, "what's open right now?")["reply"]
    )


def test_crowd_with_and_without_reports(db, seed):
    """With no reports the reply says it can't tell; with reports it gives the level and the count."""
    fountain(seed)

    assert "No recent reports" in ask(db, "is Fountain busy right now?")["reply"]

    seed.crowd(1, "crowded", NOON - timedelta(minutes=5))
    seed.crowd(1, "crowded", NOON - timedelta(minutes=2))
    reply = ask(db, "is Fountain busy right now?")["reply"]
    assert "crowded" in reply and "2 student reports" in reply


def test_it_asks_when_the_location_is_missing_or_unclear(db, seed):
    """No location, a name shared by two, and an unknown name each get a clear follow-up."""
    fountain(seed)
    seed.location(2, "Case Dining Hall", "case")
    seed.menu(21, 2, DAY, "Dinner")
    seed.item(21, "Soup")

    assert "Which dining location" in ask(db, "vegan options tonight")["reply"]
    both = ask(db, "menu at dining hall")["reply"]
    assert "Fountain Dining Hall" in both and "Case Dining Hall" in both
    assert "don't know a location" in ask(db, "menu at zzzz tonight")["reply"]


def test_a_typo_in_the_location_still_finds_it(db, seed):
    """A misspelled "fountian" still reaches Fountain's menu."""
    fountain(seed)

    assert "Steamed Rice" in ask(db, "menu at fountian tonight")["reply"]


def test_medical_safety_help_and_unknown_questions(db, seed):
    """Medical and "is it safe" questions are declined, "hello" shows examples, nonsense is not understood."""
    fountain(seed)

    assert (
        "can't give medical advice"
        in ask(db, "what medication for a reaction?")["reply"]
    )
    safety = ask(db, "is the mac and cheese safe for my dairy allergy?")["reply"]
    assert "can't tell you a dish is safe" in safety
    assert "Try:" in ask(db, "hello")["reply"]
    assert "didn't understand" in ask(db, "tell me a joke")["reply"]


def test_example_questions_name_a_real_location(db, seed):
    """Examples use a location from the database; with none, only questions that need no location."""
    empty = ask(db, "hello")["reply"]
    assert "What's open right now?" in empty
    assert "at a dining hall" not in empty.lower()
    assert "{place}" not in empty
    assert "at a dining hall" not in ask(db, "is it safe?")["reply"].lower()

    fountain(seed)

    assert "dinner at Fountain Dining Hall tonight" in ask(db, "hello")["reply"]


def test_a_reply_that_fails_the_check_is_replaced_by_the_fallback(
    db, seed, monkeypatch
):
    """If a built reply claims safety, the assistant returns the fallback and says why."""
    fountain(seed)
    monkeypatch.setattr(
        chat.answers,
        "food_filtered",
        lambda *args, **kwargs: ("Steamed Rice is safe for you.", []),
    )

    answer = ask(db, "dairy-free options at Fountain tonight")

    assert answer["source"] == "fallback"
    assert answer["reply"] == chat.answers.fallback()
    assert "safe" not in answer["reply"].lower()
    assert any("banned" in p for p in answer["problems"])


def test_how_many_dining_halls_lists_the_real_ones(db, seed):
    """A count question, even misspelled, answers with the count and the names from the database."""
    assert (
        "don't have any dining locations"
        in ask(db, "how many dining halls are there")["reply"]
    )

    fountain(seed)
    seed.location(2, "Case Dining Hall", "case")
    seed.menu(21, 2, DAY, "Dinner")
    seed.item(21, "Soup")

    reply = ask(db, "how many dinining hall are there")["reply"]

    assert "2 dining locations" in reply
    assert "- Fountain Dining Hall" in reply and "- Case Dining Hall" in reply


def test_a_recommendation_ranks_the_open_places(db, seed):
    """ "Which hall do you recommend?" names the open places, quietest first, with the facts used."""
    fountain(seed)
    seed.hours(1, DAY, "open", windows=[(420, 1260)])
    seed.location(2, "Case Dining Hall", "case")
    seed.menu(21, 2, DAY, "Dinner")
    seed.item(21, "Soup")
    seed.hours(2, DAY, "open", windows=[(420, 1260)])
    seed.crowd(1, "crowded", NOON - timedelta(minutes=3))
    seed.crowd(2, "not_busy", NOON - timedelta(minutes=3))

    reply = ask(db, "which dinning hall do you recommend")["reply"]

    assert reply.index("- Case Dining Hall") < reply.index("- Fountain Dining Hall")
    assert "open until 9:00 pm" in reply
    assert "not busy, 1 report" in reply
    assert chat.answers.LABEL_WARNING in reply


def test_a_recommendation_prefers_places_with_food_that_fits(db, seed):
    """With a saved diet, a place with nothing that fits comes after one that has food."""
    fountain(seed)  # rice fits a dairy-free diet
    seed.hours(1, DAY, "open", windows=[(420, 1260)])
    seed.location(2, "Case Dining Hall", "case")
    seed.menu(21, 2, DAY, "Dinner")
    seed.item(21, "Cheese Pizza", allergens=["dairy"])
    seed.hours(2, DAY, "open", windows=[(420, 1260)])
    seed.crowd(2, "not_busy", NOON - timedelta(minutes=3))  # quieter, but nothing fits
    saved = filter_engine.Profile(avoid=frozenset({"dairy"}))

    reply = ask(db, "which hall do you recommend?", saved)["reply"]

    assert reply.index("- Fountain Dining Hall") < reply.index("- Case Dining Hall")
    assert "1 item fits your filters" in reply
    assert "0 items fit your filters" in reply


def test_a_recommendation_says_so_when_nothing_is_open(db, seed):
    """With no place known to be open, the reply says it can't recommend one."""
    fountain(seed)

    reply = ask(db, "which hall do you recommend?")["reply"]

    assert "Nothing I know of is open right now" in reply


def test_unlabeled_menus_are_explained_instead_of_called_a_miss(db, seed):
    """When nothing can be checked, the reply says so with counts, not just "nothing fits"."""
    seed.location(1)
    seed.menu(11, 1, DAY, "Dinner")
    seed.item(11, "Bananas")
    seed.item(11, "Toast")
    saved = filter_engine.Profile(avoid=frozenset({"dairy"}))

    reply = ask(db, "what's for dinner at Fountain tonight?", saved)["reply"]

    assert (
        "Nothing at Fountain Dining Hall today for dinner fits your filters." in reply
    )
    assert "2 items can't be confirmed, for example" in reply
    assert "more item" not in reply


def test_a_short_follow_up_keeps_the_place_and_meal(db, seed):
    """ "And tomorrow?" after a question about Fountain's dinner means Fountain's dinner tomorrow."""
    fountain(seed)
    history = [{"role": "user", "text": "what's for dinner at Fountain?"}]

    reply = chat.respond(db, "and tomorrow?", None, NOON, history)["reply"]

    assert "Fountain Dining Hall" in reply
    assert "tomorrow" in reply  # no menu is loaded for tomorrow, and it says so


def test_a_follow_up_adds_a_diet_and_keeps_the_place(db, seed):
    """ "What about dairy free?" keeps the place from the question before."""
    fountain(seed)
    history = [{"role": "user", "text": "what's for dinner at Fountain tonight?"}]

    reply = chat.respond(db, "what about dairy free?", None, NOON, history)["reply"]

    assert "Steamed Rice" in reply
    assert "Mac and Cheese" not in reply


def test_a_follow_up_does_not_borrow_a_place_for_hours(db, seed):
    """ "What's open?" still means everywhere, not the last place mentioned."""
    fountain(seed)
    seed.hours(1, DAY, "open", windows=[(420, 1260)])
    history = [{"role": "user", "text": "what's for dinner at Fountain tonight?"}]

    reply = chat.respond(db, "what's open right now?", None, NOON, history)["reply"]

    assert reply.startswith("Open right now:")


def test_a_message_with_nothing_to_carry_stays_not_understood(db, seed):
    """Small talk after a food question is not turned into another food question."""
    fountain(seed)
    history = [{"role": "user", "text": "what's for dinner at Fountain tonight?"}]

    reply = chat.respond(db, "tell me a joke", None, NOON, history)["reply"]

    assert "didn't understand" in reply


def test_a_distance_question_without_a_place_asks_where_you_are(db, seed):
    """ "Which hall is close?" from "main campus" names no known place, so it asks which one."""
    fountain(seed)

    reply = ask(db, "I am in main campus which dining hall is close")["reply"]

    assert reply.startswith("Where are you?")
    assert "Talley Student Union" in reply
    assert "I don't know a location" not in reply


def test_a_named_campus_place_gets_the_closest_halls(db, seed):
    """ "Tally union" (a typo) is Talley; the hall in that building is listed with a walking estimate."""
    fountain(seed)
    seed.location(9, name="Talley – Tuffy’s Diner", slug="tuffys")
    seed.point(9, 35.78397, -78.67092)
    seed.menu(91, 9, DAY, "Dinner")
    seed.item(91, "Fries")
    seed.hours(1, DAY, windows=[(600, 1260)])
    seed.hours(9, DAY, windows=[(600, 1260)])

    reply = ask(db, "I am in Tally union which dining hall is close")["reply"]

    lines = reply.splitlines()
    assert lines[0] == "Closest to Talley Student Union:"
    assert lines[1].startswith(
        "- Talley – Tuffy’s Diner (about 1 min walk; open until 9:00 pm)"
    )
    assert lines[2].startswith("- Fountain Dining Hall (about ")
    assert "rough estimates" in reply
    assert "safe" not in reply.lower()


def test_closest_halls_prefer_the_ones_with_food_that_fits(db, seed):
    """With a saved diet, a farther hall with a fitting dish beats a nearer one with none."""
    fountain(seed)
    seed.location(9, name="Talley – Tuffy’s Diner", slug="tuffys")
    seed.point(9, 35.78397, -78.67092)
    seed.menu(91, 9, DAY, "Dinner")
    seed.nutrition("9|ice|1 cup", location_id=9, serving_size="1 cup", calories=300.0)
    seed.item(91, "Ice Cream", nutrition_key="9|ice|1 cup", allergens=["dairy"])
    for loc in (1, 9):
        seed.hours(loc, DAY, windows=[(600, 1260)])
    saved = filter_engine.Profile(avoid=frozenset({"dairy"}))

    reply = chat.respond(db, "which dining hall is near Talley", saved, NOON)["reply"]

    lines = reply.splitlines()
    assert lines[1].startswith("- Fountain Dining Hall")
    assert "1 item fits your filters" in lines[1]
    assert chat.answers.LABEL_WARNING in reply


def test_naming_a_place_after_being_asked_where_you_are(db, seed):
    """Answering "Where are you?" with just a place name gets the closest halls."""
    fountain(seed)
    asked = ask(db, "which dining hall is close")["reply"]
    history = [
        {"role": "user", "text": "which dining hall is close"},
        {"role": "assistant", "text": asked},
    ]

    reply = chat.respond(db, "Hunt Library", None, NOON, history)["reply"]

    assert reply.startswith("Closest to Hunt Library:")


def test_halls_without_coordinates_are_left_out_and_counted(db, seed):
    """A location missing from the coordinates file isn't ranked, and the reply says so."""
    fountain(seed)
    seed.location(3, name="Wolves' Den", slug="wolves")
    seed.menu(31, 3, DAY, "Dinner")
    seed.item(31, "Pasta")

    reply = ask(db, "which dining hall is closest to Hunt Library")["reply"]

    assert "- Fountain Dining Hall" in reply
    assert "Wolves' Den" not in reply
    assert "I don't have a location for 1 other place yet" in reply


def test_a_place_named_in_full_is_not_replaced_by_one_from_earlier(db, seed):
    """Asking about Atrium after a Fountain question answers about Atrium, not Fountain."""
    fountain(seed)
    seed.location(7, name="Atrium – Brickyard Pizza", slug="brickyard")
    seed.location(8, name="Atrium – Smoothie U", slug="smoothie")
    seed.menu(71, 7, DAY, "Dinner")
    seed.item(71, "Cheese Pizza")
    seed.menu(81, 8, DAY, "Dinner")
    seed.item(81, "Berry Smoothie")
    history = [{"role": "user", "text": "what's for dinner at Fountain tonight?"}]

    named = chat.respond(db, "what's at Atrium – Brickyard Pizza,", None, NOON, history)
    vague = chat.respond(db, "what's at Atrium", None, NOON, history)

    assert "Cheese Pizza" in named["reply"]
    assert "Fountain" not in named["reply"]
    assert vague["reply"].startswith("Which location do you mean")
    assert "Fountain" not in vague["reply"]


def test_outlets_a_few_metres_apart_are_listed_once(db, seed):
    """Atrium's two outlets are about 10 m apart, so only the better of them is listed."""
    for loc, name in ((7, "Atrium – Brickyard Pizza"), (8, "Atrium – Smoothie U")):
        seed.location(loc, name=name, slug=f"atrium{loc}")
        seed.point(loc, 35.78795 - loc / 1e5, -78.67065)
        seed.menu(loc * 10, loc, DAY, "Dinner")
        seed.item(loc * 10, "Snack")

    reply = ask(db, "I am at Lampe, which dining hall is close?")["reply"]

    assert reply.count("- Atrium") == 1


def test_where_can_i_eat_after_a_distance_question_is_not_about_a_made_up_place(
    db, seed
):
    """A distance question leaves no "place" behind, and "where can I eat" recommends open halls."""
    fountain(seed)
    seed.hours(1, DAY, windows=[(600, 1260)])
    history = [
        {"role": "user", "text": "I AM AT HUNT LIBRARY which dining hall is close?"},
        {"role": "assistant", "text": "Closest to Hunt Library: ..."},
    ]

    reply = chat.respond(db, "where can I eat right now?", None, NOON, history)["reply"]

    assert reply.startswith("Here's where I'd go right now:")
    assert "- Fountain Dining Hall" in reply
    assert "I don't know a location" not in reply


def three_places(seed):
    """Fountain open 9 am to 9 pm, Case closed all day, Clark with no hours stored."""
    for loc, name, slug in (
        (1, "Fountain Dining Hall", "fountain"),
        (3, "Case Dining Hall", "case"),
        (2, "Clark Dining Hall", "clark"),
    ):
        seed.location(loc, name=name, slug=slug)
        seed.menu(loc * 10, loc, DAY, "Dinner")
        seed.item(loc * 10, "Rice")
    seed.hours(1, DAY, windows=[(540, 1260)])
    seed.hours(3, DAY, status="closed")


def test_which_halls_are_open_today_lists_each_places_hours(db, seed):
    """ "Open today" gives hours for the day, not just who is open this minute."""
    three_places(seed)
    at_dawn = campus_time(datetime(2026, 10, 6, 7, 0))  # nothing is open yet

    reply = chat.respond(db, "which dining hall is open today", None, at_dawn)["reply"]

    assert reply.splitlines()[0] == "Open today:"
    assert "- Fountain Dining Hall (9:00 am to 9:00 pm)" in reply
    assert "1 place closed all day today." in reply
    assert "I don't have hours for 1 location today." in reply
    assert "Case Dining Hall" not in reply


def test_open_tomorrow_uses_tomorrows_hours(db, seed):
    """Tomorrow has no hours stored here, so every place is reported as unknown."""
    three_places(seed)

    reply = ask(db, "what's open tomorrow?")["reply"]

    assert reply.startswith("Nothing I know of is open tomorrow.")
    assert "I don't have hours for 3 locations tomorrow." in reply


def test_open_right_now_still_means_right_now(db, seed):
    """Adding "now" keeps the existing answer: who is open at this moment, until when."""
    three_places(seed)

    reply = ask(db, "which dining hall is open right now today?")["reply"]

    assert reply.splitlines()[0] == "Open right now:"
    assert "- Fountain Dining Hall, until 9:00 pm" in reply

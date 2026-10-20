# Why PackPlate

## The problem

You and three friends want lunch. One of you is vegan, one avoids nuts, one
eats halal. Where can all four of you eat, **right now**?

At NC State, answering that takes roughly **20 navigations across two
websites**. Hours are on the NC State Dining site. Menus and nutrition are on a
separate site, NetNutrition, which has no idea what time it is: it will
happily show you the full menu of a dining hall that has already closed. So
you check the hours on one site, then click location, date, and meal on the
other, for each of the five dining halls, with everyone's restrictions in mind.

Existing tools (the two official sites, and a student app that combines them)
show hours and menus, with only basic dietary filtering. None of them answer
the group question.

## Who it's for

- **Students on meal plans**, especially those living on campus who eat most
  meals in the dining halls.
- **Students with allergies**, who can be harmed by incomplete or wrong
  allergen information.
- **Students with religious or dietary restrictions:** halal, vegetarian,
  vegan.
- **Groups of friends** who need one place that works for everyone.

## What PackPlate does

- **One place for everything.** A scraper collects hours from NC State Dining
  and menus, allergens, and nutrition labels from NetNutrition into one
  database, and knows which locations are open at any moment.
- **Filters for a whole group at once.** Give it up to 10 people's needs
  (allergens to avoid, diets, protein, calorie, or sodium targets) and it
  ranks every location: places where everyone has something to eat first,
  then places that are open.
- **Never guesses that food is safe.** Every item gets one of three answers
  for each person: `fits`, `conflicts`, or `incomplete`. If the data has a gap
  (no nutrition label, an allergen icon it doesn't recognize, no diet tag), the
  answer is `incomplete`, never `fits`. A wrong "safe" can hurt someone; an
  honest "we don't know" can't.
- **Shows how busy places are**, from quick student reports (not busy,
  moderate, crowded). Recent reports count more, and nothing about the reporter
  is stored.

The website is in progress: its pages for open locations, menus, groups, and
crowd levels call this API. Your dietary profile is kept in your browser only;
the server never stores it.

## Does it work? The evidence

We didn't want to just claim PackPlate is safe, so we tested it (milestone M0,
[issue #11](https://github.com/morgansimon425/PackPlate/issues/11)). Before
running anything, we posted two targets:

| Target | Result |
|---|---|
| **Safe:** across every item PackPlate calls `fits`, 0 turn out to contain something the person avoids | ❌ **6** in 7,926 checked |
| **Useful:** at least 80% of simulated groups have somewhere everyone can eat | ✅ **100%** of 1,000 groups |

How we checked safety: a script read the ingredient list of every `fits`
answer and flagged anything that named an avoided ingredient, and a person
read every flag. The 6 real problems were all in NC State's own data: cooked
chicken fat in a soup tagged Vegetarian, whey (milk) in a pancake with no
dairy icon, sesame in garlic bread with no sesame icon, and possible peanut
oil in sunflower seeds with no nut icon. A filter that only reads the icons,
the way NetNutrition's own filter works, makes the same 6 mistakes.

**The punchline:** PackPlate can only be as safe as the data behind it, and now
we know exactly where that data fails. The next step is to read the ingredient
lists inside PackPlate itself and flag what the icons leave out
([issue #15](https://github.com/morgansimon425/PackPlate/issues/15)).
NetNutrition's filter only reads the icons, and the eval can measure whether
reading the ingredients works.

**So we fixed it and tested again.** PackPlate now reads every ingredient list
and flags what the icons leave out, the team can correct a dish's tags by hand,
and the menu warns that labels can be wrong. A second, separate test
([issue #26](https://github.com/morgansimon425/PackPlate/issues/26)) checked
today's PackPlate on new days. This time a person read the ingredients of 50
random `fits` answers, so the test doesn't rely on PackPlate's own scanner:

| Target | Result |
|---|---|
| **Safe:** 0 of 50 random `fits` answers contain something the person avoids | ✅ **0** missed (5 couldn't be told from the label) |
| **Useful:** at least 80% of simulated groups have somewhere everyone can eat | ✅ **90.2%** of 1,000 groups |

0 in 50 doesn't prove PackPlate is never wrong; it means a mistake rate of at
most 6.4%, with 95% confidence.

## Sources

- The problem, audience, and stakeholders: the
  [Project 1b report](../../proj_1b/Project_1b_Report.pdf) (Market Survey,
  Mission Statement, Stakeholders).
- What PackPlate does: the code, described in the
  [code reference](reference.md) and the [HTTP API](api.md).
- The evidence: [the M0 plan](m0-eval.md) and its results, for
  [loop 1](../eval/results.json) and [loop 2](../eval_loop2/results.json).

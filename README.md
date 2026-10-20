# 🐺 PackPlate 🍽️

<!-- Badges report the dev branch. Each links to its workflow runs on dev. -->
[![Tests](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Test count](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/EthanGoodman/723b874f576ec1c7acbc27ac884ffeca/raw/packplate-tests.json)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Ruff](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml?query=branch%3Adev)
[![Black](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml?query=branch%3Adev)
[![Prettier](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml?query=branch%3Adev)
[![ESLint](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml?query=branch%3Adev)
[![Typecheck](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml?query=branch%3Adev)
[![M0 loop 1](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml?query=branch%3Adev)
[![M0 loop 2](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_loop2.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0_loop2.yml?query=branch%3Adev)

A website that helps NC State students decide where to eat on campus. It puts
dining hours, menus, and nutrition information from every campus dining
location in one place, and filters the menus by dietary restrictions and goals
like allergies, vegetarian, halal, or a protein target. Students can enter
constraints for several people at once, so a group with different diets can
find a location where everyone has something to eat. Students can also report
how busy each location is.

## 🎯 M0: risk-killer eval

**The claim**, posted in [issue #11](https://github.com/morgansimon425/PackPlate/issues/11)
before the first run: a group of friends with different diets can find
somewhere on campus where everyone can eat, using NC State's own data, without
PackPlate ever telling someone a dish is safe when it isn't.

| Target | Result | |
|---|---|---|
| **Safe:** 0 confirmed false fits | **6** in 7,926 "fits" answers checked | ❌ missed |
| **Useful:** at least 80% of simulated groups answered | **100%** of 1,000 groups | ✅ met |

- **Safe:** every "fits" answer's ingredient list was scanned, and a person
  read every flag. The 6 real ones come from NC State's own data missing an
  allergen icon, e.g. cooked chicken fat in a soup tagged Vegetarian, and whey
  in a pancake with no dairy icon. NetNutrition's own icon-only filter makes
  the same 6 mistakes.
- **Useful:** simulated groups of 2–5 people, with restriction rates from
  published studies. These are **simulated users, not real ones**.
- **Data:** a frozen snapshot of Oct 12–14, 2026, committed to the repo.
- **Reproduce:** `cd proj_2 && python -m eval.m0`. The **M0 loop 1** badge
  means the committed numbers reproduce, not that the targets were met.
- **Details:** [the plan](proj_2/docs/m0-eval.md),
  [the result](proj_2/eval/results.json), and the review decision in
  [issue #11](https://github.com/morgansimon425/PackPlate/issues/11).

### Loop 2: after the fixes

Loop 1 showed that NC State's icons leave allergens out, so PackPlate now reads
the ingredient lists itself and flags what the icons miss
([#17](https://github.com/morgansimon425/PackPlate/pull/17), tuned in
[#20](https://github.com/morgansimon425/PackPlate/pull/20)), lets the team
correct a dish's tags by hand
([#19](https://github.com/morgansimon425/PackPlate/pull/19)), and warns on the
menu that labels can be wrong
([#23](https://github.com/morgansimon425/PackPlate/pull/23)). Loop 2 re-tests
today's PackPlate on new days, with targets posted in
[issue #26](https://github.com/morgansimon425/PackPlate/issues/26) before the
run. Because the new scanner was built from loop 1's word list, loop 2 doesn't
use a word list: a person read the ingredients of 50 random "fits" answers.

| Target | Result | |
|---|---|---|
| **Safe:** 0 missed in 50 random "fits" answers | **0** missed (45 ok, 5 unclear) | ✅ met |
| **Useful:** at least 80% of simulated groups answered | **90.2%** of 1,000 groups | ✅ met |

- **Safe:** 0 misses in 45 decided answers means the true miss rate is at most
  6.4% (95% confidence), not that it's 0. The 5 unclear answers list "natural
  flavors" for a pork, halal, vegan, or vegetarian profile, where the label
  can't tell.
- **Useful:** lower than loop 1's 100%. The days and the filter both changed,
  so the eval can't say how much of the drop each one caused.
- **Data:** a frozen snapshot of Oct 20–22, 2026, committed to the repo.
- **Reproduce:** `cd proj_2 && python -m eval_loop2.m0`. It has its own
  **M0 loop 2** badge and shares no code with loop 1.
- **Details:** [the plan and limits](proj_2/docs/m0-eval.md#loop-2-after-the-fixes)
  and [the result](proj_2/eval_loop2/results.json).

## 📚 Documentation

| | |
|---|---|
| [Why PackPlate](proj_2/docs/why.md) | The problem, who it's for, and the evidence that it works |
| [How to use it](proj_2/docs/how.md) | Worked examples: the website, the API, and common developer tasks |
| [Code reference](proj_2/docs/reference.md) | Every module, class, and function, generated from the code |
| [HTTP API](proj_2/docs/api.md) | Every endpoint and data model, generated from the API |
| [Install](INSTALL.md) | Getting PackPlate running on your machine |
| [Contributing](CONTRIBUTING.md) | Setup, tests, checkers, and how to make changes safely |
| [Code of conduct](CODE-OF-CONDUCT.md) · [License](LICENSE.md) · [Third-party libraries](THIRD_PARTY_LIBRARIES.md) | |

## 📁 Structure

```
proj_1b/    Project 1b — requirements
proj_2/     Project 2 — implementation (Next.js + FastAPI + Postgres)
```

## 🎓 Course

CSC 510 Software Engineering, NC State University, Fall 2026.
Course repository: https://github.com/txt/se26f

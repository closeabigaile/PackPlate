# 🐺 PackPlate 🍽️

<!-- Badges report the dev branch. Each links to its workflow runs on dev. -->
[![Tests](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Test count](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/EthanGoodman/723b874f576ec1c7acbc27ac884ffeca/raw/packplate-tests.json)](https://github.com/morgansimon425/PackPlate/actions/workflows/tests.yml?query=branch%3Adev)
[![Ruff](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/ruff.yml?query=branch%3Adev)
[![Black](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/black.yml?query=branch%3Adev)
[![Prettier](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/prettier.yml?query=branch%3Adev)
[![ESLint](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/eslint.yml?query=branch%3Adev)
[![Typecheck](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/typecheck.yml?query=branch%3Adev)
[![M0 eval](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml/badge.svg?branch=dev)](https://github.com/morgansimon425/PackPlate/actions/workflows/m0.yml?query=branch%3Adev)

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
- **Reproduce:** `cd proj_2 && python -m eval.m0`. The **M0 eval** badge
  means the committed numbers reproduce, not that the targets were met.
- **Details:** [the plan](proj_2/docs/m0-eval.md),
  [the result](proj_2/eval/results.json), and the review decision in
  [issue #11](https://github.com/morgansimon425/PackPlate/issues/11).

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

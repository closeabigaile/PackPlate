# 13 — M5 meal comparison and integration

|                        |                        |
| ---------------------- | ---------------------- |
| **Author**       | Supreme Constantine    |
| **Date**         | 2026-11-24             |
| **Tool / model** | ChatGPT (GPT-6 series) |

## 1. Request

I used ChatGPT to help plan and implement M5, which focused on
helping users find healthier meal options across campus based on
their nutrition goals and dietary preferences.

I also used it for help understanding the existing codebase,
writing tests, debugging, and integrating M5 with the other
Project 3 features.

## 2. AI proposal

The AI suggested creating a recommendation service, an API endpoint,
and a frontend page for finding and comparing meals.

It proposed using the existing dietary filter engine before ranking
meals based on protein, calories, or sodium. It also provided guidance
on Git branching, integration, and testing.

## 3. Human review

- Reviewed the existing repository before implementing the feature.
- Kept the recommendation feature within the scope of the existing
  PackPlate application.
- Reviewed the implementation against the expected user workflow.
- Worked through integration issues with the other Project 3 features.
- Used Git to review and submit changes through the team's workflow.

## 4. Final version

M5 includes a rule-based recommendation engine, a recommendation API,
and a frontend interface for finding and comparing meals.

Users can select a nutrition goal, date, and meal period. Their saved
dietary preferences are applied to recommendations.

The feature was integrated with account-based dietary profile storage
and merged into dev.

Initial implementation commit: `51a695f`.

Integration pull request: #10.

## 5. Verification

- [X] Reviewed the source code and implementation.
- [X] Reviewed Git history and integration status.
- [X] Confirmed integration into dev.
- [X] Confirmed the presence of recommendation and profile test files.

The repository contains 21 related test functions across
test_recommendations.py, test_recommendations_api.py, and
test_profile_api.py.

See [M5 documentation](../../docs/m5-meal-comparison.md) for the
implementation details and limitations.

ChatGPT assisted with drafting and updating Project 3 documentation. All documentation and code quality checks passed, with 12 tests passing and 9 skipped due to database configuration.

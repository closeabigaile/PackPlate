# M5 — Smart meal comparison and dietary profile integration

**Status (2026-11-24):** Implementation and account integration merged into
`dev` through PR #10.

## Goal

Help students find meals across NC State dining locations that match their
dietary preferences and nutrition goals without having to search through
each location's menu individually.

## Features

- Ranked meal recommendations across campus dining locations.
- Three nutrition goals: high protein, lower calories, and lower sodium.
- Filtering by menu date and meal period.
- Automatic application of saved dietary preferences.
- Side-by-side nutritional comparison of two meals.
- Account-based dietary profile storage.

## How recommendations work

The recommendation engine retrieves available menu items for the selected
date and meal period.

Items are checked against the user's dietary profile using PackPlate's
existing filter engine. Items marked as conflicting or incomplete are
excluded, along with items missing reliable nutrition data for the
selected goal.

Eligible items are ranked according to the selected nutrition goal:

| Goal | Ranking |
|---|---|
| High protein | Highest protein first |
| Lower calories | Lowest calories first |
| Lower sodium | Lowest sodium first |

Identical dishes at the same location with the same listed serving size
are grouped together while retaining their meal periods.

The API returns up to 20 recommendations.

## Meal comparison

The Compare Meals page allows users to select two recommended meals and
compare their nutritional information side by side.

The comparison includes calories, protein, carbohydrates, fat, sodium,
and serving size. Missing values are displayed as N/A rather than zero.

Nutrition values are based on the listed serving sizes, which may differ
between meals.

## Dietary profile integration

M5 builds on the account system introduced in M1.

Users who are not signed in can continue saving their dietary preferences
in their browser. Signed-in users can save their preferences to their
account and retrieve them after signing in again.

The frontend synchronizes the account profile with the browser's profile
so existing dietary filtering features can continue using it.

Logging out clears the account's profile from the browser without
deleting the saved account profile.

See [m1-accounts.md](m1-accounts.md) for additional details about account
and profile synchronization.

## Implementation

| File | Responsibility |
|---|---|
| `backend/app/services/recommendations.py` | Dietary filtering and nutrition-based ranking |
| `backend/app/api/recommendations.py` | Recommendation endpoint and response construction |
| `backend/app/schemas/recommendations.py` | Request and response schemas |
| `frontend/src/app/compare/page.tsx` | Recommendation interface and meal comparison |
| `backend/app/api/profile.py` | Account-based profile storage endpoints |
| `frontend/src/lib/accountProfile.ts` | Synchronization between account and browser profiles |

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/recommendations` | Retrieve ranked meal recommendations |
| GET | `/profile` | Retrieve the signed-in user's profile |
| PUT | `/profile` | Save or replace a dietary profile |
| DELETE | `/profile` | Remove a saved dietary profile |

The profile endpoints require authentication. The recommendation endpoint
accepts an optional dietary profile in its request body.

See [how.md](how.md) for usage examples.

## Testing

Automated tests for M5 are located in:

- `backend/tests/test_recommendations.py`
- `backend/tests/test_recommendations_api.py`
- `backend/tests/test_profile_api.py`

These provide service-level and API-level test coverage for the
recommendation and dietary profile functionality.

M5 was also integrated with the other Project 3 features before being
merged into `dev`.

## Limitations

- Recommendations depend on available menu and nutrition data.
- Nutrition values are based on listed serving sizes.
- Dietary compatibility does not guarantee allergen safety.
- Recommendations do not currently account for travel distance or
  create complete daily meal plans.
- The feature uses rule-based ranking rather than machine learning.

## Checklist

- [x] Nutrition-based recommendation engine
- [x] Dietary compatibility filtering
- [x] Recommendation API
- [x] Meal comparison interface
- [x] Account-based dietary profile integration
- [x] Automated test files
- [x] Integration into dev
- [x] User and milestone documentation

# M2: Predicted crowd levels

**Owner:** Satwi

**Goal:** Improve the busyness estimates without asking students to report how busy a location is.

**What was added:** A crowd forecast for every open location, predicted from the time of day and the location's opening hours. The `/locations` API has a new `forecast` field (`level`, `estimate`, `source`), and the How Busy page shows a "predicted" badge. The existing `crowd` field and the student report buttons still work, and recent reports adjust the prediction when there are any.

**How it works:** Weekday and weekend meal rushes (breakfast, lunch, dinner) set the base level. It is lowered in the first and last 30 minutes of an open period, and no prediction is shown when a location is closed or its hours are unknown. The score becomes not busy, moderate, or crowded.

**Verification:** 13 unit tests for the prediction logic and 3 API tests for the `forecast` field. The unit tests pass locally, and the API tests run in CI.

**Limitations:** The meal-rush times and cut-offs are hand-tuned guesses and have not yet been compared with real crowds. The campus calendar list for breaks and exam weeks is empty until someone adds the dates.

**Code:** `backend/app/services/crowd_forecast.py`, `backend/app/api/locations.py`, and the How Busy page in the frontend.

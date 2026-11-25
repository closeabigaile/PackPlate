import type { LocationSummary } from "./types";

// All-you-care-to-eat dining halls vs. everything else (food court counters,
// cafés, markets). NC State's data has no such field, so it's by name: the
// dining halls are called "... Dining Hall", plus On the Oval.
const OTHER_DINING_HALLS = new Set(["On the Oval"]);

export type LocationKind = "hall" | "other";

export function locationKind(location: LocationSummary): LocationKind {
  return /dining hall/i.test(location.name) ||
    OTHER_DINING_HALLS.has(location.name)
    ? "hall"
    : "other";
}

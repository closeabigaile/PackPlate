import { allergenLabel, dietLabel } from "./diet";

// Short badge text for why an item can't be shown as a fit, from the reason the
// API gives (backend/app/services/filter_engine.py). Like campus menu apps such
// as Nutrislice, a badge names the specific thing that's uncertain instead of a
// generic "unknown"; the full reason is in the item's details.
export function shortReason(reason: string): string {
  let m: RegExpMatchArray | null;
  if (reason.startsWith("unrecognized trait")) return "Unknown allergen";
  if (reason.startsWith("no nutrition label")) return "No nutrition label";
  if ((m = reason.match(/may contain (\w+)$/))) {
    return `May contain ${allergenLabel(m[1])}`;
  }
  if ((m = reason.match(/^tagged (\w+), but/))) {
    return `May not be ${dietLabel(m[1])}`;
  }
  if ((m = reason.match(/^not labeled (\w+)$/))) {
    return `Not labeled ${dietLabel(m[1])}`;
  }
  if ((m = reason.match(/^(\w+) not published$/))) {
    return `${m[1][0].toUpperCase()}${m[1].slice(1)} not listed`;
  }
  return reason[0].toUpperCase() + reason.slice(1);
}

/** Badge text for a list of reasons: the first one, plus how many more. */
export function reasonSummary(reasons: string[]): string {
  if (reasons.length === 0) return "Check the label";
  const more = reasons.length - 1;
  return more > 0
    ? `${shortReason(reasons[0])} +${more} more`
    : shortReason(reasons[0]);
}

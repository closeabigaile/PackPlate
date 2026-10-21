// Display names and order for NetNutrition stations (MenuItem.course).
//
// NC State mixes real stations ("Grill Stations", "Deli") with internal recipe
// categories ("ENTREE - POULTRY", "Display", "None"). This maps them to clean
// section names, merges duplicates, and orders sections like a menu: mains
// first, add-ons and uncategorized items last. Data is never changed, only shown.

export const OTHER = "Other";
export const TOPPINGS = "Toppings & Sauces";

const RENAMED: Record<string, string> = {
  // NC State's "Display" holds made-to-order items: omelets, burgers, tacos.
  Display: "Made to Order",
  Extras: TOPPINGS,
  "Salad Bar Toppings": TOPPINGS,
  "Salad Dressings": TOPPINGS,
  Sauces: TOPPINGS,
  "BEVERAGE HOT": "Hot Drinks",
};

// Lower comes first; anything not listed (named stations) sits in the middle.
const RANK: Record<string, number> = {
  Entrées: 0,
  "Made to Order": 1,
  Sides: 3,
  Soup: 3,
  Salad: 3,
  Desserts: 4,
  "Hot Drinks": 5,
  [TOPPINGS]: 6,
  [OTHER]: 7,
};
const STATION_RANK = 2;

function titleCase(text: string): string {
  return text.toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
}

// Joins a station and its subsection in a label: "Flashpoint › Entrées".
export const SUB = " › ";

function tidy(name: string): string {
  const cased = name === name.toUpperCase() ? titleCase(name) : name;
  return cased
    .replace(/home style/i, "Homestyle")
    .replace(/\bentree\b/i, "Entrées");
}

/**
 * The section name to show for an item's NetNutrition station. Stations with
 * parts ("Flashpoint - Entree", "Flashpoint - Sides") become one station with
 * subsections: "Flashpoint › Entrées".
 */
export function stationLabel(course: string | null): string {
  if (!course || course === "None") return OTHER;
  if (RENAMED[course]) return RENAMED[course];
  if (course === "Home Style Entree") return "Homestyle";
  if (/^entree\b/i.test(course)) return "Entrées";
  if (/^dessert\b/i.test(course)) return "Desserts";
  // A hyphen followed by a space separates station and part ("Newton's- Grill");
  // a hyphen inside a word doesn't ("Gluten-Friendly Station").
  const parts = course.match(/^(.+?)\s*-\s+(.+)$/);
  if (parts) return `${tidy(parts[1].trim())}${SUB}${tidy(parts[2].trim())}`;
  return tidy(course);
}

/** [station, subsection or null] for a label from stationLabel. */
export function splitLabel(label: string): [string, string | null] {
  const [station, sub] = label.split(SUB);
  return [station, sub ?? null];
}

/** Sort order for a label from stationLabel (by its station). */
export function stationRank(label: string): number {
  return RANK[splitLabel(label)[0]] ?? STATION_RANK;
}

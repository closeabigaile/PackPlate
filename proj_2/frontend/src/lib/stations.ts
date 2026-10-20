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

/** The section name to show for an item's NetNutrition station. */
export function stationLabel(course: string | null): string {
  if (!course || course === "None") return OTHER;
  if (RENAMED[course]) return RENAMED[course];
  if (/^entree\b/i.test(course) || course === "Home Style Entree") {
    return "Entrées";
  }
  if (/^dessert\b/i.test(course)) return "Desserts";
  return course === course.toUpperCase() ? titleCase(course) : course;
}

/** Sort order for a section name from stationLabel. */
export function stationRank(label: string): number {
  return RANK[label] ?? STATION_RANK;
}

// Types for the PackPlate API.
//
// These mirror backend/app/schemas/*.py field for field. They are written by
// hand because they could not be generated in the environment this was built
// in. To replace them with generated types, run `npm run gen:api` (backend
// running on :8000) and import from src/lib/api-schema.d.ts instead. Until
// then, if a backend schema changes, change it here too.

export type CrowdLevel = "not_busy" | "moderate" | "crowded";
export type Allergen =
  "dairy" | "egg" | "gluten" | "nuts" | "pork" | "seafood" | "sesame" | "soy";
export type Diet = "halal" | "vegan" | "vegetarian";
export type Verdict = "fits" | "conflicts" | "incomplete";

// schemas/crowd.py
export interface Crowd {
  level: CrowdLevel | null; // null = no recent reports: unknown, not "not busy"
  report_count: number;
  last_reported_at: string | null;
}

// schemas/meta.py
export interface Freshness {
  last_run_finished_at: string | null;
  last_run_status: "ok" | "partial" | null;
  stale: boolean;
  stale_after_hours: number;
}

// schemas/locations.py
export interface Period {
  opens_at: string;
  closes_at: string;
}

export interface HoursDay {
  date: string; // YYYY-MM-DD
  status: "open" | "closed" | "unknown";
  periods: Period[];
  raw_text: string | null;
}

export interface LocationSummary {
  id: number;
  name: string;
  description: string | null;
  dining_url: string | null;
  is_open: boolean | null; // null = today's hours are unknown
  closes_at: string | null;
  opens_next_at: string | null;
  today: HoursDay;
  crowd: Crowd;
}

export interface MenuSummary {
  id: number;
  date: string; // YYYY-MM-DD
  meal: string;
  scraped: boolean; // false = listed, items not scraped yet
}

export interface LocationDetail extends LocationSummary {
  hours: HoursDay[];
  menus: MenuSummary[];
}

export interface Nutrition {
  serving_size: string | null;
  calories: number | null;
  protein_g: number | null;
  fat_g: number | null;
  carbs_g: number | null;
  sodium_mg: number | null;
  ingredients: string | null;
  contains: string[];
  missing_fields: string[];
  fetched_at: string;
}

export interface MenuItem {
  id: number;
  name: string;
  course: string | null;
  serving_size: string | null;
  allergens: string[];
  diets: string[];
  unrecognized_traits: string[];
  nutrition: Nutrition | null; // null = no label, allergens come from icons only
}

export interface Menu extends MenuSummary {
  items: MenuItem[];
}

// schemas/filters.py
export interface Profile {
  name?: string | null;
  avoid: Allergen[];
  diets: Diet[];
  min_protein_g?: number | null;
  max_calories?: number | null;
  max_sodium_mg?: number | null;
}

export interface FilterRequest {
  profiles: Profile[];
}

export interface ItemResult {
  verdict: Verdict;
  reasons: string[];
}

export interface FilteredItem extends MenuItem {
  results: ItemResult[]; // one per profile, in request order
}

export interface FilteredMenu extends MenuSummary {
  items: FilteredItem[];
}

export interface ProfileCounts {
  name: string | null;
  fits: number;
  incomplete: number;
  conflicts: number;
}

export interface GroupLocation {
  id: number;
  name: string;
  is_open: boolean | null;
  closes_at: string | null;
  opens_next_at: string | null;
  items_checked: number;
  everyone_fits: boolean;
  profiles: ProfileCounts[];
}

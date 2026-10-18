import type { Allergen, CrowdLevel, Diet, Profile } from "./types";

// Keys must match the backend (schemas/filters.py). An unknown key is a 422.
export const ALLERGENS: { key: Allergen; label: string; note?: string }[] = [
  { key: "dairy", label: "Dairy" },
  { key: "egg", label: "Egg" },
  { key: "gluten", label: "Gluten" },
  { key: "nuts", label: "Nuts", note: "peanuts and tree nuts" },
  { key: "pork", label: "Pork" },
  { key: "seafood", label: "Seafood", note: "fish and shellfish" },
  { key: "sesame", label: "Sesame" },
  { key: "soy", label: "Soy" },
];

export const DIETS: { key: Diet; label: string }[] = [
  { key: "vegetarian", label: "Vegetarian" },
  { key: "vegan", label: "Vegan" },
  { key: "halal", label: "Halal" },
];

export const MAX_PROFILES = 10;
export const MAX_NAME_LENGTH = 50;

// Server-side limits for the numeric goals.
export const LIMITS = {
  min_protein_g: 1000,
  max_calories: 10000,
  max_sodium_mg: 100000,
} as const;

export const CROWD_LABELS: Record<CrowdLevel, string> = {
  not_busy: "Not busy",
  moderate: "Moderate",
  crowded: "Crowded",
};

export function emptyProfile(): Profile {
  return { name: "", avoid: [], diets: [] };
}

export function hasConstraints(profile: Profile): boolean {
  return (
    profile.avoid.length > 0 ||
    profile.diets.length > 0 ||
    profile.min_protein_g != null ||
    profile.max_calories != null ||
    profile.max_sodium_mg != null
  );
}

// The shape the API accepts: no empty name, no stray fields.
export function toRequestProfile(profile: Profile): Profile {
  const name = profile.name?.trim();
  return {
    ...(name ? { name: name.slice(0, MAX_NAME_LENGTH) } : {}),
    avoid: profile.avoid,
    diets: profile.diets,
    min_protein_g: profile.min_protein_g ?? null,
    max_calories: profile.max_calories ?? null,
    max_sodium_mg: profile.max_sodium_mg ?? null,
  };
}

function numberInRange(value: unknown, max: number): number | null {
  return typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= max
    ? value
    : null;
}

// Reads whatever is in storage and keeps only values the API would accept, so
// old or hand-edited data can never cause a 422 or an accidental "fits".
export function parseProfile(raw: string | null): Profile {
  if (!raw) return emptyProfile();
  try {
    const data: unknown = JSON.parse(raw);
    if (typeof data !== "object" || data === null) return emptyProfile();
    const record = data as Record<string, unknown>;
    const allergenKeys = new Set<string>(ALLERGENS.map((a) => a.key));
    const dietKeys = new Set<string>(DIETS.map((d) => d.key));
    const avoid = Array.isArray(record.avoid)
      ? record.avoid.filter((v): v is Allergen => typeof v === "string" && allergenKeys.has(v))
      : [];
    const diets = Array.isArray(record.diets)
      ? record.diets.filter((v): v is Diet => typeof v === "string" && dietKeys.has(v))
      : [];
    return {
      name: typeof record.name === "string" ? record.name.slice(0, MAX_NAME_LENGTH) : "",
      avoid,
      diets,
      min_protein_g: numberInRange(record.min_protein_g, LIMITS.min_protein_g),
      max_calories: numberInRange(record.max_calories, LIMITS.max_calories),
      max_sodium_mg: numberInRange(record.max_sodium_mg, LIMITS.max_sodium_mg),
    };
  } catch {
    return emptyProfile();
  }
}

// A message if a number is outside what the API accepts, else null.
export function validateProfile(profile: Profile): string | null {
  const checks: [number | null | undefined, number, string][] = [
    [profile.min_protein_g, LIMITS.min_protein_g, "Minimum protein"],
    [profile.max_calories, LIMITS.max_calories, "Maximum calories"],
    [profile.max_sodium_mg, LIMITS.max_sodium_mg, "Maximum sodium"],
  ];
  for (const [value, max, label] of checks) {
    if (value != null && !(Number.isFinite(value) && value >= 0 && value <= max)) {
      return `${label} must be a number from 0 to ${max.toLocaleString("en-US")}.`;
    }
  }
  return null;
}

export function allergenLabel(key: string): string {
  return ALLERGENS.find((a) => a.key === key)?.label ?? key;
}

export function dietLabel(key: string): string {
  return DIETS.find((d) => d.key === key)?.label ?? key;
}

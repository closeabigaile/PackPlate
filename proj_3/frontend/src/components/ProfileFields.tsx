"use client";

import { ALLERGENS, DIETS, LIMITS, MAX_NAME_LENGTH } from "@/lib/diet";
import type { Allergen, Diet, Profile } from "@/lib/types";

type NumberField = "min_protein_g" | "max_calories" | "max_sodium_mg";

// The form controls for one person's dietary profile. Used on My Dietary
// Profile and for each person on Eat as a Group, so both behave identically.
export function ProfileFields({
  idPrefix,
  value,
  onChange,
  showName = false,
}: {
  idPrefix: string;
  value: Profile;
  onChange: (next: Profile) => void;
  showName?: boolean;
}) {
  function toggleAvoid(key: Allergen) {
    const avoid = value.avoid.includes(key)
      ? value.avoid.filter((k) => k !== key)
      : [...value.avoid, key];
    onChange({ ...value, avoid });
  }

  function toggleDiet(key: Diet) {
    const diets = value.diets.includes(key)
      ? value.diets.filter((k) => k !== key)
      : [...value.diets, key];
    onChange({ ...value, diets });
  }

  function setNumber(field: NumberField, raw: string) {
    onChange({ ...value, [field]: raw === "" ? null : Number(raw) });
  }

  return (
    <div className="form">
      {showName ? (
        <div className="field">
          <label htmlFor={`${idPrefix}-name`}>Name (optional)</label>
          <input
            id={`${idPrefix}-name`}
            className="input"
            type="text"
            maxLength={MAX_NAME_LENGTH}
            value={value.name ?? ""}
            onChange={(event) =>
              onChange({ ...value, name: event.target.value })
            }
          />
        </div>
      ) : null}

      <fieldset>
        <legend>Allergies: avoid these</legend>
        <div className="chips">
          {ALLERGENS.map((allergen) => (
            <label key={allergen.key} className="chip">
              <input
                type="checkbox"
                checked={value.avoid.includes(allergen.key)}
                onChange={() => toggleAvoid(allergen.key)}
              />
              <span>{allergen.label}</span>
            </label>
          ))}
        </div>
        <p className="help">
          “Nuts” covers peanuts and tree nuts, and “Seafood” covers fish and
          shellfish. NC State’s data can’t tell them apart.
        </p>
      </fieldset>

      <fieldset>
        <legend>Dietary preferences</legend>
        <div className="chips">
          {DIETS.map((diet) => (
            <label key={diet.key} className="chip">
              <input
                type="checkbox"
                checked={value.diets.includes(diet.key)}
                onChange={() => toggleDiet(diet.key)}
              />
              <span>{diet.label}</span>
            </label>
          ))}
        </div>
        <p className="help">
          An item only counts as fitting a diet if it is tagged with it. If you
          pick more than one, an item has to meet all of them.
        </p>
      </fieldset>

      <fieldset>
        <legend>Nutrition goals per item (optional)</legend>
        <div className="number-grid">
          <div className="field">
            <label htmlFor={`${idPrefix}-protein`}>Minimum protein (g)</label>
            <input
              id={`${idPrefix}-protein`}
              className="input"
              type="number"
              inputMode="decimal"
              min={0}
              max={LIMITS.min_protein_g}
              value={value.min_protein_g ?? ""}
              onChange={(event) =>
                setNumber("min_protein_g", event.target.value)
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${idPrefix}-calories`}>Maximum calories</label>
            <input
              id={`${idPrefix}-calories`}
              className="input"
              type="number"
              inputMode="decimal"
              min={0}
              max={LIMITS.max_calories}
              value={value.max_calories ?? ""}
              onChange={(event) =>
                setNumber("max_calories", event.target.value)
              }
            />
          </div>
          <div className="field">
            <label htmlFor={`${idPrefix}-sodium`}>Maximum sodium (mg)</label>
            <input
              id={`${idPrefix}-sodium`}
              className="input"
              type="number"
              inputMode="decimal"
              min={0}
              max={LIMITS.max_sodium_mg}
              value={value.max_sodium_mg ?? ""}
              onChange={(event) =>
                setNumber("max_sodium_mg", event.target.value)
              }
            />
          </div>
        </div>
      </fieldset>
    </div>
  );
}

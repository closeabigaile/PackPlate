"use client";

import { useState } from "react";
import { Bar, NUTRIENTS } from "@/components/NutritionBars";
import { PageShell } from "@/components/PageShell";
import { StateMessage } from "@/components/StateMessage";
import { formatNumber } from "@/lib/format";
import { nowMs } from "@/lib/now";
import { api, errorMessage } from "@/lib/api";
import { useSavedProfile } from "@/lib/profileStore";
import type { NutritionGoal, RecommendationItem } from "@/lib/types";
import Link from "next/link";

const goals: { value: NutritionGoal; label: string }[] = [
  { value: "high_protein", label: "High protein" },
  { value: "lower_calories", label: "Lower calories" },
  { value: "lower_sodium", label: "Lower sodium" },
];

function mealKey(item: RecommendationItem): string {
  return `${item.location_id}:${item.meal_periods.join(", ")}:${item.item_id}`;
}

export default function ComparePage() {
  const [goal, setGoal] = useState<NutritionGoal>("high_protein");
  const [date, setDate] = useState(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/New_York",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date(nowMs())),
  );
  const [meal, setMeal] = useState("");
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);
  const [selectedMeals, setSelectedMeals] = useState<string[]>([]);

  const savedProfile = useSavedProfile();

  function toggleMealSelection(key: string) {
    setSelectedMeals((current) => {
      if (current.includes(key)) {
        return current.filter((id) => id !== key);
      }

      if (current.length >= 2) return current;

      return [...current, key];
    });
  }

  async function findMeals() {
    setLoading(true);
    setError("");
    setSearched(false);
    setSelectedMeals([]);
    setResults([]);

    try {
      const response = await api.recommendations({
        goal,
        meal: meal || null,
        date,
        profile: savedProfile,
      });

      setResults(response.recommendations);

      setSearched(true);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const comparedMeals = selectedMeals
    .map((key) => results.find((item) => mealKey(item) === key))
    .filter((item): item is RecommendationItem => item !== undefined);

  return (
    <PageShell
      title="Compare meals"
      icon="compare"
      lede="Find meals across campus that match a nutrition goal, then compare them side by side."
      showFreshness={false}
    >
      <section className="panel">
        <h2 className="section-title">Find meals</h2>

        <div className="form">
          <div className="form-grid">
            <div className="field">
              <label htmlFor="nutrition-goal">Nutrition goal</label>
              <select
                id="nutrition-goal"
                className="input"
                value={goal}
                onChange={(e) => setGoal(e.target.value as NutritionGoal)}
              >
                {goals.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="comparison-date">Menu date</label>
              <input
                id="comparison-date"
                type="date"
                className="input"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="meal-period">Meal period</label>
              <select
                id="meal-period"
                className="input"
                value={meal}
                onChange={(e) => setMeal(e.target.value)}
              >
                <option value="">All meals</option>
                <option value="breakfast">Breakfast</option>
                <option value="brunch">Brunch</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="late night">Late night</option>
                <option value="daily">Daily</option>
              </select>
            </div>
          </div>

          <div className="form">
            <div className="comparison-profile-note">
              <p>
                Your saved dietary preferences are automatically applied to
                recommendations.
              </p>
              <Link href="/profile">Update my diet</Link>
            </div>

            <div className="button-row">
              <button
                type="button"
                className="btn"
                onClick={findMeals}
                disabled={loading}
              >
                {loading ? "Finding meals…" : "Find meals"}
              </button>
            </div>
          </div>
        </div>
      </section>

      {error && (
        <div className="state-message error" role="alert">
          {error}
        </div>
      )}

      {!searched && !loading && !error ? (
        <section className="how-it-works" aria-labelledby="how-title">
          <h2 id="how-title" className="section-title">
            How it works
          </h2>
          <ol className="steps">
            <li>
              <span className="step-num" aria-hidden="true">
                1
              </span>
              <strong>Pick a goal</strong>
              <span className="meta">
                High protein, fewer calories or less sodium.
              </span>
            </li>
            <li>
              <span className="step-num" aria-hidden="true">
                2
              </span>
              <strong>See the best matches</strong>
              <span className="meta">
                Ranked across every location with a menu that day, after your
                saved diet is applied.
              </span>
            </li>
            <li>
              <span className="step-num" aria-hidden="true">
                3
              </span>
              <strong>Compare two</strong>
              <span className="meta">
                Add any two meals to see their nutrition side by side.
              </span>
            </li>
          </ol>
        </section>
      ) : null}

      {loading ? (
        <StateMessage kind="loading">Finding meals…</StateMessage>
      ) : null}

      {searched && (
        <section>
          <h2 className="section-title">
            Recommended meals
            <span className="count">({results.length} found)</span>
          </h2>

          {results.length === 0 ? (
            <div className="state-message">
              No eligible meals found. Try another nutrition goal, meal period
              or date.
            </div>
          ) : (
            <ul className="result-grid">
              {results.map((item) => {
                const picked = selectedMeals.includes(mealKey(item));
                return (
                  <li
                    key={`${item.location_id}-${item.meal_periods.join(", ")}-${item.item_id}`}
                    className={
                      picked ? "panel meal-card is-picked" : "panel meal-card"
                    }
                  >
                    <div className="meal-card-head">
                      <span className="rank" aria-label={`Rank ${item.rank}`}>
                        {item.rank}
                      </span>
                      <div>
                        <h3 className="location-name">{item.name}</h3>
                        <p className="meta">
                          {item.location_name} · {item.meal_periods.join(", ")}
                        </p>
                      </div>
                    </div>

                    <dl className="stat-row">
                      <div>
                        <dt>Calories</dt>
                        <dd>{formatNumber(item.nutrition.calories, "")}</dd>
                      </div>
                      <div>
                        <dt>Protein</dt>
                        <dd>{formatNumber(item.nutrition.protein_g, " g")}</dd>
                      </div>
                      <div>
                        <dt>Sodium</dt>
                        <dd>{formatNumber(item.nutrition.sodium_mg, " mg")}</dd>
                      </div>
                    </dl>

                    <p className="meal-reason">{item.reason}</p>
                    <p className="help">
                      Serving: {item.nutrition.serving_size ?? "not listed"}
                    </p>

                    <button
                      type="button"
                      className="btn btn-small btn-outline"
                      aria-pressed={picked}
                      disabled={selectedMeals.length >= 2 && !picked}
                      onClick={() => toggleMealSelection(mealKey(item))}
                    >
                      {picked ? "Remove from comparison" : "Add to comparison"}
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      )}

      {comparedMeals.length > 0 && (
        <section className="panel" aria-labelledby="side-title">
          <h2 id="side-title" className="section-title">
            Side-by-side comparison
          </h2>

          {comparedMeals.length < 2 ? (
            <p className="help">
              Add one more meal to compare their nutrition.
            </p>
          ) : (
            <>
              <p className="help">
                Per listed serving. Serving sizes may differ between meals.
              </p>
              <ul className="compare-legend">
                {comparedMeals.map((item, i) => (
                  <li key={mealKey(item)}>
                    <span
                      className={`legend-swatch legend-${i}`}
                      aria-hidden="true"
                    />
                    <strong>{item.name}</strong>
                    <span className="meta">
                      {" "}
                      · {item.location_name} · serving{" "}
                      {item.nutrition.serving_size ?? "not listed"}
                    </span>
                  </li>
                ))}
              </ul>
              <dl className="compare-bars">
                {NUTRIENTS.map((n) => {
                  const values = comparedMeals.map(
                    (item) => item.nutrition[n.key],
                  );
                  const top = Math.max(n.max, ...values.map((v) => v ?? 0));
                  return (
                    <div key={n.key} className="compare-row">
                      <dt>{n.label}</dt>
                      <dd>
                        {comparedMeals.map((item, i) => {
                          const value = item.nutrition[n.key];
                          return (
                            <span key={mealKey(item)} className="compare-line">
                              {value === null ? (
                                <span
                                  className="bar bar-empty"
                                  aria-hidden="true"
                                />
                              ) : (
                                <Bar
                                  value={value}
                                  max={top}
                                  tone={i === 0 ? "red" : "teal"}
                                />
                              )}
                              <span className="bar-value">
                                <span className="visually-hidden">
                                  {item.name}:{" "}
                                </span>
                                {formatNumber(value, n.unit)}
                              </span>
                            </span>
                          );
                        })}
                      </dd>
                    </div>
                  );
                })}
              </dl>
            </>
          )}
        </section>
      )}
    </PageShell>
  );
}

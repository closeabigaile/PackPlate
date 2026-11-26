import type { CSSProperties } from "react";
import { formatNumber } from "@/lib/format";
import type { Nutrition } from "@/lib/types";

// Nutrition as short bars. Each bar is scaled to a rough per-meal reference
// (not a daily value, and not advice): it only makes numbers quicker to compare.
// A missing number says "not listed" and has no bar, never a bar at zero.
export const NUTRIENTS = [
  { key: "calories", label: "Calories", unit: "", max: 900, tone: "red" },
  { key: "protein_g", label: "Protein", unit: " g", max: 50, tone: "green" },
  { key: "carbs_g", label: "Carbs", unit: " g", max: 100, tone: "amber" },
  { key: "fat_g", label: "Fat", unit: " g", max: 45, tone: "purple" },
  { key: "sodium_mg", label: "Sodium", unit: " mg", max: 1500, tone: "teal" },
] as const;

export type NutrientKey = (typeof NUTRIENTS)[number]["key"];

export function Bar({
  value,
  max,
  tone,
}: {
  value: number;
  max: number;
  tone: string;
}) {
  return (
    <span className="bar" aria-hidden="true">
      <span
        className={`bar-fill bar-${tone}`}
        style={
          {
            "--w": `${Math.max(3, Math.min(100, (value / max) * 100))}%`,
          } as CSSProperties
        }
      />
    </span>
  );
}

export function NutritionBars({ nutrition }: { nutrition: Nutrition }) {
  return (
    <div className="nutrition-bars">
      <p className="help">Serving: {nutrition.serving_size ?? "not listed"}</p>
      <dl className="bar-list">
        {NUTRIENTS.map((n) => {
          const value = nutrition[n.key];
          return (
            <div key={n.key} className="bar-row">
              <dt>{n.label}</dt>
              <dd>
                {value === null ? (
                  <span className="bar bar-empty" aria-hidden="true" />
                ) : (
                  <Bar value={value} max={n.max} tone={n.tone} />
                )}
                <span className="bar-value">{formatNumber(value, n.unit)}</span>
              </dd>
            </div>
          );
        })}
      </dl>
    </div>
  );
}

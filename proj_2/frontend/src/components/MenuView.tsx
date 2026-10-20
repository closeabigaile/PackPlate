"use client";

import { useState } from "react";
import { ALLERGENS, allergenLabel, dietLabel } from "@/lib/diet";
import { formatNumber } from "@/lib/format";
import { stationLabel, stationRank } from "@/lib/stations";
import { reasonSummary, shortReason } from "@/lib/verdicts";
import type { ItemResult, MenuItem, MenuSummary, Nutrition } from "@/lib/types";
import { StateMessage } from "./StateMessage";
import { VerdictBadge } from "./Badges";

// Works for plain menus and for menus already checked against one profile
// (FilteredMenu), which add `results` to each item.
export interface ViewItem extends MenuItem {
  results?: ItemResult[];
}
export interface ViewMenu extends MenuSummary {
  items: ViewItem[];
}

function NutritionTable({ nutrition }: { nutrition: Nutrition }) {
  const rows: [string, string][] = [
    ["Serving size", nutrition.serving_size ?? "not listed"],
    ["Calories", formatNumber(nutrition.calories, "")],
    ["Protein", formatNumber(nutrition.protein_g, " g")],
    ["Fat", formatNumber(nutrition.fat_g, " g")],
    ["Carbs", formatNumber(nutrition.carbs_g, " g")],
    ["Sodium", formatNumber(nutrition.sodium_mg, " mg")],
  ];
  return (
    <div>
      <table className="nutrition-table">
        <caption className="visually-hidden">Nutrition facts</caption>
        <tbody>
          {rows.map(([label, value]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              <td>{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {nutrition.missing_fields.length > 0 ? (
        <p className="help">
          The label doesn’t give: {nutrition.missing_fields.join(", ")}.
        </p>
      ) : null}
      {nutrition.ingredients ? (
        <p className="help">Ingredients: {nutrition.ingredients}</p>
      ) : null}
    </div>
  );
}

// Allergens the ingredients mention that NC State's label doesn't list.
function possibleAllergens(item: ViewItem): [string, string[]][] {
  const flags = item.nutrition?.ingredient_flags ?? {};
  return ALLERGENS.filter(
    (a) => flags[a.key] && !item.allergens.includes(a.key),
  ).map((a) => [a.key, flags[a.key]]);
}

const VERDICT_ORDER = { fits: 0, incomplete: 1, conflicts: 2 } as const;

function rank(item: ViewItem): number {
  const verdict = item.results?.[0]?.verdict;
  return verdict ? VERDICT_ORDER[verdict] : 0;
}

// "Serving (16oz)" -> "16 oz"; the full serving text if there's no size in it.
function sizeLabel(item: ViewItem, index: number): string {
  const inner = item.serving_size?.match(/\(([^)]*)\)\s*$/)?.[1]?.trim();
  const text = inner || item.serving_size || `Size ${index + 1}`;
  return text.replace(/(\d)([a-z])/i, "$1 $2");
}

// One listing per dish. NC State lists each size of a dish (16 oz, 24 oz) as a
// separate item with its own label; `sizes` holds them all. The details show
// the chosen size; with a profile, the listing opens on the best-fitting size
// and warns about any size that fits worse.
function Item({ sizes }: { sizes: ViewItem[] }) {
  const best = sizes.reduce((b, s, i) => (rank(s) < rank(sizes[b]) ? i : b), 0);
  const [chosen, setChosen] = useState(best);
  const item = sizes[chosen];
  const result = item.results?.[0];
  const tone = result ? `item item-${result.verdict}` : "item";
  const possible = possibleAllergens(item);
  const removed = Object.entries(item.diets_removed ?? {});
  const worse = sizes
    .map((s, i) => ({ s, i }))
    .filter(({ s }) => s.results && rank(s) > rank(sizes[best]));

  return (
    <li className={tone}>
      <details>
        <summary>
          <span className="item-name">{item.name}</span>
          {result ? (
            <VerdictBadge verdict={result.verdict} reasons={result.reasons} />
          ) : null}
          {item.diets.map((diet) => (
            <span key={diet} className="pill pill-diet">
              {dietLabel(diet)}
            </span>
          ))}
          {possible.length > 0 ? (
            <span className="pill pill-warn">Check label</span>
          ) : null}
          {worse.length > 0 ? (
            <span className="pill pill-warn">
              {sizeLabel(worse[0].s, worse[0].i)}:{" "}
              {reasonSummary(worse[0].s.results?.[0]?.reasons ?? [])}
            </span>
          ) : null}
        </summary>

        <div className="item-detail">
          {sizes.length > 1 ? (
            <div className="chips" role="radiogroup" aria-label="Size">
              {sizes.map((s, i) => (
                <label key={s.id} className="chip">
                  <input
                    type="radio"
                    name={`size-${sizes[0].id}`}
                    checked={i === chosen}
                    onChange={() => setChosen(i)}
                  />
                  <span>{sizeLabel(s, i)}</span>
                </label>
              ))}
            </div>
          ) : null}

          {worse.length > 0 ? (
            <div className="banner banner-warn">
              Sizes differ for your profile:
              <ul>
                {worse.map(({ s, i }) => (
                  <li key={s.id}>
                    {sizeLabel(s, i)}:{" "}
                    {(s.results?.[0]?.reasons ?? [])
                      .map(shortReason)
                      .join(", ")}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {result && result.reasons.length > 0 ? (
            <ul className="reasons">
              {result.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          ) : null}

          <p>
            <strong>Contains: </strong>
            {item.allergens.length === 0 ? (
              <span>no allergens listed</span>
            ) : (
              item.allergens.map((allergen) => (
                <span key={allergen} className="pill pill-allergen">
                  {allergenLabel(allergen)}
                </span>
              ))
            )}
          </p>

          {possible.length > 0 ? (
            <p className="banner banner-warn">
              The ingredients mention{" "}
              {possible
                .map(
                  ([key, words]) =>
                    `${words.join(", ")} (${allergenLabel(key)})`,
                )
                .join("; ")}
              , which NC State’s label doesn’t list. Check the label or ask
              dining staff.
            </p>
          ) : null}

          {removed.length > 0 ? (
            <p className="banner banner-warn">
              NC State lists this as{" "}
              {removed.map(([diet]) => dietLabel(diet)).join(" and ")}, but
              PackPlate doesn’t: {removed[0][1]}.
            </p>
          ) : null}

          {item.unrecognized_traits.length > 0 ? (
            <p className="banner banner-warn">
              Also tagged {item.unrecognized_traits.join(", ")}. PackPlate can’t
              check these, so treat this item’s allergen information as
              incomplete.
            </p>
          ) : null}

          {item.nutrition ? (
            <NutritionTable nutrition={item.nutrition} />
          ) : (
            <p className="banner banner-warn">
              No nutrition label for this item, so allergens come from icons
              only. Don’t rely on it if you have an allergy.
            </p>
          )}
        </div>
      </details>
    </li>
  );
}

// Items grouped under clean section names (lib/stations.ts), in menu order,
// with the sizes of each dish (same name in the same section) kept together.
function groupByCourse(items: ViewItem[]): [string, ViewItem[][]][] {
  const groups = new Map<string, Map<string, ViewItem[]>>();
  for (const item of items) {
    const label = stationLabel(item.course);
    const dishes = groups.get(label) ?? new Map<string, ViewItem[]>();
    groups.set(label, dishes);
    const key = item.name.trim().toLowerCase();
    dishes.set(key, [...(dishes.get(key) ?? []), item]);
  }
  return [...groups.entries()]
    .map(([label, dishes]): [string, ViewItem[][]] => [
      label,
      [...dishes.values()],
    ])
    .sort(([a], [b]) => stationRank(a) - stationRank(b));
}

// Meal tabs in the order a day runs; NC State's "Daily" menu is served all day.
const MEAL_ORDER = ["Breakfast", "Brunch", "Lunch", "Dinner", "Daily"];

function mealOrder(meal: string): number {
  const i = MEAL_ORDER.indexOf(meal);
  return i === -1 ? MEAL_ORDER.length : i;
}

function mealName(meal: string): string {
  return meal === "Daily" ? "All Day" : meal;
}

// For today's menus, the meal that's on now or next (by campus time); for other
// days, the first meal. Only picks which tab opens first.
function defaultMeal(menus: ViewMenu[]): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date());
  const get = (type: string) => parts.find((p) => p.type === type)?.value;
  const today = `${get("year")}-${get("month")}-${get("day")}`;
  const minutes = Number(get("hour")) * 60 + Number(get("minute"));
  if (menus[0].date !== today) return menus[0].meal;
  const now = minutes < 630 ? "Breakfast" : minutes < 960 ? "Lunch" : "Dinner";
  return menus.some((m) => m.meal === now) ? now : menus[0].meal;
}

function MenuBody({
  menu,
  hideConflicts,
}: {
  menu: ViewMenu;
  hideConflicts: boolean;
}) {
  if (!menu.scraped) {
    return (
      <p className="banner banner-warn">
        This menu is listed, but its items haven’t been loaded yet.
      </p>
    );
  }
  const sections = groupByCourse(menu.items).map(
    ([course, dishes]): [string, ViewItem[][]] => [
      course,
      // With a profile: fits first, then needs a check, then doesn't fit (by
      // each dish's best size; ties keep NC State's order). A dish is hidden
      // only when none of its sizes fit.
      dishes
        .filter(
          (sizes) =>
            !hideConflicts ||
            sizes.some((s) => s.results?.[0]?.verdict !== "conflicts"),
        )
        .sort((a, b) => Math.min(...a.map(rank)) - Math.min(...b.map(rank))),
    ],
  );
  const total = groupByCourse(menu.items).reduce(
    (n, [, dishes]) => n + dishes.length,
    0,
  );
  const hidden = total - sections.reduce((n, [, d]) => n + d.length, 0);

  return (
    <>
      {hidden > 0 ? (
        <p className="help">
          {hidden} item{hidden === 1 ? "" : "s"} hidden because{" "}
          {hidden === 1 ? "it doesn’t" : "they don’t"} fit your profile.
        </p>
      ) : null}
      {sections.map(([course, dishes]) =>
        dishes.length === 0 ? null : (
          <div key={course}>
            <h5 className="course-title">{course}</h5>
            <ul className="item-list">
              {dishes.map((sizes) => (
                <Item key={sizes[0].id} sizes={sizes} />
              ))}
            </ul>
          </div>
        ),
      )}
    </>
  );
}

export function MenuView({
  menus,
  hideConflicts = false,
}: {
  menus: ViewMenu[];
  hideConflicts?: boolean;
}) {
  const [chosen, setChosen] = useState<string | null>(null);
  // Meals NC State lists with no items aren't shown.
  const shown = menus
    .filter((menu) => !menu.scraped || menu.items.length > 0)
    .sort((a, b) => mealOrder(a.meal) - mealOrder(b.meal));
  if (shown.length === 0) {
    return (
      <StateMessage kind="empty">No menu is listed for this day.</StateMessage>
    );
  }

  const meal = shown.some((m) => m.meal === chosen)
    ? chosen
    : defaultMeal(shown);
  const menu = shown.find((m) => m.meal === meal) ?? shown[0];

  return (
    <div className="stack">
      {shown.length > 1 ? (
        <div className="meal-tabs" role="tablist" aria-label="Meal">
          {shown.map((m) => (
            <button
              key={m.id}
              type="button"
              role="tab"
              aria-selected={m.id === menu.id}
              className="meal-tab"
              onClick={() => setChosen(m.meal)}
            >
              {mealName(m.meal)}
            </button>
          ))}
        </div>
      ) : (
        <h4 className="meal-title">All Day</h4>
      )}
      <section aria-label={mealName(menu.meal)}>
        <MenuBody menu={menu} hideConflicts={hideConflicts} />
      </section>
    </div>
  );
}

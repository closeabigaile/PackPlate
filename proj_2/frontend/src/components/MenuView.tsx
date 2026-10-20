import { allergenLabel, dietLabel } from "@/lib/diet";
import { formatNumber } from "@/lib/format";
import { startsCollapsed, stationLabel, stationRank } from "@/lib/stations";
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

function Item({ item }: { item: ViewItem }) {
  const result = item.results?.[0];
  const tone = result ? `item item-${result.verdict}` : "item";

  return (
    <li className={tone}>
      <details>
        <summary>
          <span className="item-name">{item.name}</span>
          {result ? <VerdictBadge verdict={result.verdict} /> : null}
          {item.diets.map((diet) => (
            <span key={diet} className="pill pill-diet">
              {dietLabel(diet)}
            </span>
          ))}
        </summary>

        <div className="item-detail">
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

// Items grouped under clean section names (lib/stations.ts), in menu order.
function groupByCourse(items: ViewItem[]): [string, ViewItem[]][] {
  const groups = new Map<string, ViewItem[]>();
  for (const item of items) {
    const label = stationLabel(item.course);
    const existing = groups.get(label);
    if (existing) existing.push(item);
    else groups.set(label, [item]);
  }
  return [...groups.entries()].sort(
    ([a], [b]) => stationRank(a) - stationRank(b),
  );
}

export function MenuView({
  menus,
  hideConflicts = false,
}: {
  menus: ViewMenu[];
  hideConflicts?: boolean;
}) {
  // Meals NC State lists with no items aren't shown.
  const shown = menus.filter((menu) => !menu.scraped || menu.items.length > 0);
  if (shown.length === 0) {
    return (
      <StateMessage kind="empty">No menu is listed for this day.</StateMessage>
    );
  }

  return (
    <div className="stack">
      {shown.map((menu) => {
        const visible = hideConflicts
          ? menu.items.filter(
              (item) => item.results?.[0]?.verdict !== "conflicts",
            )
          : menu.items;
        const hidden = menu.items.length - visible.length;

        return (
          <section key={menu.id} aria-label={menu.meal}>
            <h4 className="meal-title">
              {shown.length === 1 ? "All Day" : menu.meal}
            </h4>

            {!menu.scraped ? (
              <p className="banner banner-warn">
                This menu is listed, but its items haven’t been loaded yet.
              </p>
            ) : menu.items.length === 0 ? (
              <p className="meta">No items on this menu.</p>
            ) : (
              <>
                {hidden > 0 ? (
                  <p className="help">
                    {hidden} item{hidden === 1 ? "" : "s"} hidden because{" "}
                    {hidden === 1 ? "it doesn’t" : "they don’t"} fit your
                    profile.
                  </p>
                ) : null}
                {groupByCourse(visible).map(([course, items]) => {
                  const list = (
                    <ul className="item-list">
                      {items.map((item) => (
                        <Item key={item.id} item={item} />
                      ))}
                    </ul>
                  );
                  return startsCollapsed(course) ? (
                    <details key={course}>
                      <summary className="course-title">
                        {course} ({items.length})
                      </summary>
                      {list}
                    </details>
                  ) : (
                    <div key={course}>
                      <h5 className="course-title">{course}</h5>
                      {list}
                    </div>
                  );
                })}
              </>
            )}
          </section>
        );
      })}
    </div>
  );
}

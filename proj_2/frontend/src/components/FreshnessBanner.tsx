"use client";

import { api } from "@/lib/api";
import { formatAge } from "@/lib/format";
import { useAsync } from "@/lib/useAsync";

// Defined outside the component so reading the clock is not part of rendering.
async function loadFreshness() {
  const freshness = await api.freshness();
  const ageHours = freshness.last_run_finished_at
    ? (Date.now() - new Date(freshness.last_run_finished_at).getTime()) / 3_600_000
    : null;
  return { freshness, ageHours };
}

// Says how old the dining data is, and warns when it is stale, never loaded,
// or only partly loaded. Shown on every page that depends on scraped data.
export function FreshnessBanner() {
  const { data, error } = useAsync(loadFreshness, "freshness");

  if (error) {
    return (
      <p className="banner banner-warn" role="status">
        <strong>Couldn’t check how recent the data is.</strong> Hours and menus
        may be out of date. Check dining.ncsu.edu for today’s hours.
      </p>
    );
  }
  if (!data) return null;

  const { freshness, ageHours } = data;

  if (freshness.last_run_finished_at === null || ageHours === null) {
    return (
      <p className="banner banner-warn" role="status">
        <strong>No dining data has been loaded yet.</strong> Hours and menus
        will be missing until the first update finishes.
      </p>
    );
  }

  const partial =
    freshness.last_run_status === "partial"
      ? " The last update was partial, so some locations may be missing or older."
      : "";

  if (freshness.stale) {
    return (
      <p className="banner banner-warn" role="status">
        <strong>This data may be out of date.</strong> It was last updated{" "}
        {formatAge(ageHours)}.{partial} Check dining.ncsu.edu for today’s hours.
      </p>
    );
  }

  return (
    <p className={partial ? "banner banner-warn" : "banner"} role="status">
      Hours and menus last updated {formatAge(ageHours)}.{partial}
    </p>
  );
}

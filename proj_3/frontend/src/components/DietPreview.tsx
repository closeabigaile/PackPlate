"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { hasConstraints, toRequestProfile, validateProfile } from "@/lib/diet";
import { formatDay } from "@/lib/format";
import { locationKind } from "@/lib/locationKind";
import type { LocationSummary, Profile, Verdict } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { Icon } from "./Icon";

// How many days ahead to look, and how many dishes make a "real" menu day
// (a holiday can list a single dish, which says little about a profile).
const LOOKAHEAD = 7;
const FULL_DAY = 10;

interface Preview {
  date: string;
  counts: Record<Verdict, number>;
  total: number;
}

// The location to preview: an open dining hall if there is one, else any
// dining hall, else the first location.
function pickLocation(list: LocationSummary[]): LocationSummary | null {
  const halls = list.filter((l) => locationKind(l) === "hall");
  return halls.find((l) => l.is_open === true) ?? halls[0] ?? list[0] ?? null;
}

// Checks the draft profile against the first of the next few days with a
// full menu (else the fullest one found), and counts dishes (each name once)
// by verdict. Usually that's today: one request.
async function loadPreview(
  locationId: number,
  profile: Profile,
): Promise<Preview | null> {
  const detail = await api.location(locationId);
  const dates = [
    ...new Set(
      detail.menus
        .filter((m) => m.scraped && m.date >= detail.today.date)
        .map((m) => m.date),
    ),
  ]
    .sort()
    .slice(0, LOOKAHEAD);
  let fallback: Preview | null = null;
  for (const date of dates) {
    const menus = await api.filterMenus(locationId, [profile], date);
    const best = new Map<string, Verdict>();
    const order: Record<Verdict, number> = {
      fits: 0,
      incomplete: 1,
      conflicts: 2,
    };
    for (const menu of menus) {
      for (const item of menu.items) {
        const verdict = item.results[0]?.verdict;
        if (!verdict) continue;
        const key = item.name.trim().toLowerCase();
        const seen = best.get(key);
        if (!seen || order[verdict] < order[seen]) best.set(key, verdict);
      }
    }
    if (best.size > 0) {
      const counts = { fits: 0, incomplete: 0, conflicts: 0 };
      best.forEach((v) => (counts[v] += 1));
      const found = { date, counts, total: best.size };
      if (found.total >= FULL_DAY) return found;
      if (!fallback || found.total > fallback.total) fallback = found;
    }
  }
  return fallback;
}

// Waits until `value` has stopped changing for `ms`, so typing in a number
// field doesn't send a request per keystroke.
function useSettled<T>(value: T, ms: number): T {
  const [settled, setSettled] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setSettled(value), ms);
    return () => clearTimeout(timer);
  }, [value, ms]);
  return settled;
}

export function DietPreview({ profile }: { profile: Profile }) {
  const locations = useAsync(api.locations, "locations");
  const [chosenId, setChosenId] = useState<number | null>(null);
  const all = locations.data ?? [];
  const location =
    all.find((l) => l.id === chosenId) ?? pickLocation(all) ?? null;

  const ready = hasConstraints(profile) && validateProfile(profile) === null;
  const request = JSON.stringify(toRequestProfile(profile));
  const settled = useSettled(request, 450);

  const preview = useAsync(
    () =>
      location && ready
        ? loadPreview(location.id, JSON.parse(settled) as Profile)
        : Promise.resolve(null),
    `diet-preview-${location?.id ?? "none"}-${ready}-${settled}`,
  );

  if (!location) return null;

  return (
    <section className="panel diet-preview" aria-live="polite">
      <div className="diet-preview-head">
        <p className="eyebrow">Live preview</p>
        <label className="diet-preview-pick">
          <span className="meta">at</span>
          <select
            className="input input-small"
            aria-label="Location to preview"
            value={location.id}
            onChange={(event) => setChosenId(Number(event.target.value))}
          >
            {all.map((l) => (
              <option key={l.id} value={l.id}>
                {l.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!ready ? (
        <p className="help">
          <Icon name="info" size={16} /> Pick an allergy, a diet or a goal to
          see how many dishes at {location.name} would fit you.
        </p>
      ) : preview.loading || settled !== request ? (
        <p className="help">Checking {location.name}…</p>
      ) : preview.error ? (
        <p className="help">Couldn’t check a menu just now.</p>
      ) : preview.data == null ? (
        <p className="help">
          {location.name} has no menu items for the next few days.
        </p>
      ) : (
        <>
          <p className="diet-preview-headline">
            <strong>
              {preview.data.counts.fits} of {preview.data.total}
            </strong>{" "}
            dishes at {location.name} fit this profile on{" "}
            {formatDay(preview.data.date)}
          </p>
          <span className="fit-bar" aria-hidden="true">
            <span
              className="fit-seg fit-ok"
              style={{ flexGrow: preview.data.counts.fits }}
            />
            <span
              className="fit-seg fit-warn"
              style={{ flexGrow: preview.data.counts.incomplete }}
            />
            <span
              className="fit-seg fit-bad"
              style={{ flexGrow: preview.data.counts.conflicts }}
            />
          </span>
          <p className="meta">
            {preview.data.counts.incomplete} need a check ·{" "}
            {preview.data.counts.conflicts} don’t fit ·{" "}
            <Link href={`/menus?location=${location.id}`} className="text-link">
              See the menu
            </Link>
          </p>
        </>
      )}
    </section>
  );
}

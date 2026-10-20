"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import {
  allergenLabel,
  dietLabel,
  hasConstraints,
  toRequestProfile,
} from "@/lib/diet";
import { formatDay } from "@/lib/format";
import { useSavedProfile } from "@/lib/profileStore";
import type { LocationDetail, LocationSummary, Profile } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { StatusPill } from "./Badges";
import { MenuView, type ViewMenu } from "./MenuView";
import { StateMessage } from "./StateMessage";

function describeProfile(profile: Profile): string {
  const parts: string[] = [];
  if (profile.avoid.length > 0) {
    parts.push(`avoiding ${profile.avoid.map(allergenLabel).join(", ")}`);
  }
  if (profile.diets.length > 0) {
    parts.push(profile.diets.map(dietLabel).join(" + "));
  }
  if (profile.min_protein_g != null)
    parts.push(`at least ${profile.min_protein_g} g protein`);
  if (profile.max_calories != null)
    parts.push(`under ${profile.max_calories} calories`);
  if (profile.max_sodium_mg != null)
    parts.push(`under ${profile.max_sodium_mg} mg sodium`);
  return parts.join("; ");
}

// The menus for one day at one location, with a date picker.
function MenuDay({
  detail,
  profile,
  hideConflicts,
}: {
  detail: LocationDetail;
  profile: Profile | null;
  hideConflicts: boolean;
}) {
  const today = detail.today.date;
  const dates = [...new Set(detail.menus.map((menu) => menu.date))];

  // Open (or opening later today): today's menu. Closed for the day: the next
  // day that has a menu, which is what the "future menu" dropdown is for.
  const defaultDate =
    detail.is_open === false && detail.opens_next_at === null
      ? (dates.find((d) => d > today) ?? today)
      : today;

  const [chosen, setChosen] = useState<string | null>(null);
  const date = chosen ?? defaultDate;
  const options = dates.includes(date) ? dates : [date, ...dates];

  const key = `menus-${detail.id}-${date}-${profile ? JSON.stringify(profile) : "plain"}`;
  const menus = useAsync<ViewMenu[]>(
    () =>
      profile
        ? api.filterMenus(detail.id, [profile], date)
        : api.menus(detail.id, date),
    key,
  );

  return (
    <>
      <div className="toolbar">
        <div className="field">
          <label htmlFor={`date-${detail.id}`}>Menu for</label>
          <select
            id={`date-${detail.id}`}
            className="input"
            value={date}
            onChange={(event) => setChosen(event.target.value)}
          >
            {options.map((d) => (
              <option key={d} value={d}>
                {formatDay(d)}
                {d === today ? " (today)" : ""}
              </option>
            ))}
          </select>
        </div>
      </div>

      {menus.error ? (
        <StateMessage kind="error" onRetry={menus.reload}>
          {menus.error}
        </StateMessage>
      ) : !menus.data ? (
        <StateMessage kind="loading">Loading menu…</StateMessage>
      ) : (
        <MenuView
          menus={menus.data}
          hideConflicts={hideConflicts && profile !== null}
        />
      )}
    </>
  );
}

// Fetches the location's detail (for the dates that have menus), then shows it.
function LocationMenus({
  location,
  profile,
  hideConflicts,
}: {
  location: LocationSummary;
  profile: Profile | null;
  hideConflicts: boolean;
}) {
  const detail = useAsync(
    () => api.location(location.id),
    `location-${location.id}`,
  );

  if (detail.error) {
    return (
      <StateMessage kind="error" onRetry={detail.reload}>
        {detail.error}
      </StateMessage>
    );
  }
  if (!detail.data)
    return <StateMessage kind="loading">Loading menu…</StateMessage>;
  return (
    <MenuDay
      detail={detail.data}
      profile={profile}
      hideConflicts={hideConflicts}
    />
  );
}

// A dropdown for one location. Nothing is fetched until it is opened.
function LocationPanel({
  location,
  defaultOpen,
  profile,
  hideConflicts,
}: {
  location: LocationSummary;
  defaultOpen: boolean;
  profile: Profile | null;
  hideConflicts: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const panelId = `menu-panel-${location.id}`;

  return (
    <div className="accordion">
      <h3>
        <button
          type="button"
          className="accordion-head"
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((value) => !value)}
        >
          <span className="accordion-title">
            <span className="location-name">{location.name}</span>
            <StatusPill isOpen={location.is_open} />
          </span>
          <span className="chevron" aria-hidden="true">
            ▾
          </span>
        </button>
      </h3>
      {open ? (
        <div id={panelId} className="accordion-body">
          {location.dining_url ? (
            <div className="row-links">
              <a
                href={location.dining_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Dining page <span aria-hidden="true">↗</span>
                <span className="visually-hidden"> (opens in a new tab)</span>
              </a>
            </div>
          ) : null}
          <LocationMenus
            location={location}
            profile={profile}
            hideConflicts={hideConflicts}
          />
        </div>
      ) : null}
    </div>
  );
}

export function MenusBrowser({
  initialLocationId,
}: {
  initialLocationId: number | null;
}) {
  const locations = useAsync(api.locations, "locations");
  const saved = useSavedProfile();
  const [applyProfile, setApplyProfile] = useState(true);
  const [hideConflicts, setHideConflicts] = useState(false);

  const constrained = hasConstraints(saved);
  const profile = applyProfile && constrained ? toRequestProfile(saved) : null;

  const open = locations.data?.filter((l) => l.is_open === true) ?? [];
  const closed = locations.data?.filter((l) => l.is_open === false) ?? [];
  const unknown = locations.data?.filter((l) => l.is_open === null) ?? [];

  function renderPanels(list: LocationSummary[]) {
    return list.map((location) => (
      <LocationPanel
        key={location.id}
        location={location}
        defaultOpen={location.id === initialLocationId}
        profile={profile}
        hideConflicts={hideConflicts}
      />
    ));
  }

  return (
    <>
      <section className="panel" aria-label="Dietary profile">
        {constrained ? (
          <div className="stack">
            <label className="checkbox-line">
              <input
                type="checkbox"
                checked={applyProfile}
                onChange={(event) => setApplyProfile(event.target.checked)}
              />
              Check items against my dietary profile
            </label>
            {applyProfile ? (
              <>
                <p className="help">
                  Using your profile: {describeProfile(saved)}.{" "}
                  <Link
                    href="/profile"
                    style={{ color: "var(--red)", fontWeight: 600 }}
                  >
                    Edit
                  </Link>
                </p>
                <label className="checkbox-line">
                  <input
                    type="checkbox"
                    checked={hideConflicts}
                    onChange={(event) => setHideConflicts(event.target.checked)}
                  />
                  Hide items that don’t fit (items we can’t confirm stay
                  visible)
                </label>
              </>
            ) : null}
          </div>
        ) : (
          <p className="help">
            Showing every item.{" "}
            <Link
              href="/profile"
              style={{ color: "var(--red)", fontWeight: 600 }}
            >
              Set your dietary profile
            </Link>{" "}
            to see which items fit you.
          </p>
        )}
      </section>

      {locations.error ? (
        <StateMessage kind="error" onRetry={locations.reload}>
          {locations.error}
        </StateMessage>
      ) : !locations.data ? (
        <StateMessage kind="loading">Loading locations…</StateMessage>
      ) : locations.data.length === 0 ? (
        <StateMessage kind="empty">
          No dining locations have been loaded yet.
        </StateMessage>
      ) : (
        <>
          <section aria-labelledby="open-menus-title">
            <h2 id="open-menus-title" className="section-title">
              Open locations <span className="count">({open.length})</span>
            </h2>
            <p className="help" style={{ marginBottom: "0.6rem" }}>
              Open a location to see its menu for today.
            </p>
            {open.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is open right now.
              </StateMessage>
            ) : (
              <div className="stack">{renderPanels(open)}</div>
            )}
          </section>

          {unknown.length > 0 ? (
            <section aria-labelledby="unknown-menus-title">
              <h2 id="unknown-menus-title" className="section-title">
                Hours unknown <span className="count">({unknown.length})</span>
              </h2>
              <div className="stack">{renderPanels(unknown)}</div>
            </section>
          ) : null}

          <section aria-labelledby="closed-menus-title">
            <h2 id="closed-menus-title" className="section-title">
              Closed locations <span className="count">({closed.length})</span>
            </h2>
            <p className="help" style={{ marginBottom: "0.6rem" }}>
              Open a location to see its next menu, and pick another day if you
              like.
            </p>
            {closed.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is closed right now.
              </StateMessage>
            ) : (
              <div className="stack">{renderPanels(closed)}</div>
            )}
          </section>
        </>
      )}
    </>
  );
}

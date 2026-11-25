"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import {
  allergenLabel,
  dietLabel,
  hasConstraints,
  toRequestProfile,
} from "@/lib/diet";
import { formatDay, formatHours, formatTime } from "@/lib/format";
import { useSavedProfile } from "@/lib/profileStore";
import type { LocationDetail, LocationSummary, Profile } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";
import { StatusPill } from "./Badges";
import { Icon } from "./Icon";
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

// "Closes at 8:00 PM", "Opens again at 7:00 AM", or the day's hours.
function shortWhen(location: LocationSummary): string {
  if (location.is_open === true && location.closes_at) {
    return `Until ${formatTime(location.closes_at)}`;
  }
  if (location.is_open === false) {
    return location.opens_next_at
      ? `Opens ${formatTime(location.opens_next_at)}`
      : "Closed for today";
  }
  return "Hours unknown";
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

// The chosen location: its name and hours on top, its menu below.
function MenuPane({
  location,
  profile,
  hideConflicts,
}: {
  location: LocationSummary;
  profile: Profile | null;
  hideConflicts: boolean;
}) {
  return (
    <section
      className="panel menu-pane"
      aria-labelledby={`menu-title-${location.id}`}
    >
      <div className="menu-pane-head">
        <div>
          <h2 id={`menu-title-${location.id}`} className="menu-pane-title">
            {location.name}
          </h2>
          <p className="meta">Today: {formatHours(location.today)}</p>
        </div>
        <div className="menu-pane-actions">
          <StatusPill isOpen={location.is_open} />
          {location.dining_url ? (
            <a
              href={location.dining_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-small btn-quiet"
            >
              Dining page <span aria-hidden="true">↗</span>
              <span className="visually-hidden"> (opens in a new tab)</span>
            </a>
          ) : null}
        </div>
      </div>
      <LocationMenus
        location={location}
        profile={profile}
        hideConflicts={hideConflicts}
      />
    </section>
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
  const [chosenId, setChosenId] = useState<number | null>(initialLocationId);

  const constrained = hasConstraints(saved);
  const profile = applyProfile && constrained ? toRequestProfile(saved) : null;

  const all = locations.data ?? [];
  const groups = [
    { title: "Open now", list: all.filter((l) => l.is_open === true) },
    { title: "Hours unknown", list: all.filter((l) => l.is_open === null) },
    { title: "Closed", list: all.filter((l) => l.is_open === false) },
  ].filter((g) => g.list.length > 0);

  // The linked or picked location, else the first open one, else the first.
  const selected =
    all.find((l) => l.id === chosenId) ?? groups[0]?.list[0] ?? null;

  // Bring the chosen location into view inside the list (sideways on phones),
  // scrolling only the list itself, never the page.
  const pickerRef = useRef<HTMLElement>(null);
  const selectedId = selected?.id ?? null;
  useEffect(() => {
    const nav = pickerRef.current;
    const button = nav?.querySelector<HTMLElement>('[aria-pressed="true"]');
    if (!nav || !button) return;
    const n = nav.getBoundingClientRect();
    const b = button.getBoundingClientRect();
    if (b.left < n.left || b.right > n.right) {
      nav.scrollLeft += b.left - n.left - 16;
    }
    if (b.top < n.top || b.bottom > n.bottom) {
      nav.scrollTop += b.top - n.top - 40;
    }
  }, [selectedId]);

  return (
    <>
      <section className="panel profile-bar" aria-label="Dietary profile">
        {constrained ? (
          <div className="profile-bar-inner">
            <label className="toggle">
              <input
                type="checkbox"
                checked={applyProfile}
                onChange={(event) => setApplyProfile(event.target.checked)}
              />
              <span className="toggle-track" aria-hidden="true" />
              Check items against my diet
            </label>
            {applyProfile ? (
              <>
                <p className="help">
                  {describeProfile(saved)}.{" "}
                  <Link href="/profile" className="text-link">
                    Edit
                  </Link>
                </p>
                <label className="toggle">
                  <input
                    type="checkbox"
                    checked={hideConflicts}
                    onChange={(event) => setHideConflicts(event.target.checked)}
                  />
                  <span className="toggle-track" aria-hidden="true" />
                  Hide items that don’t fit (items that need a check stay
                  visible)
                </label>
              </>
            ) : null}
          </div>
        ) : (
          <p className="help">
            <Icon name="info" size={16} /> Showing every item.{" "}
            <Link href="/profile" className="text-link">
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
      ) : selected === null ? (
        <StateMessage kind="empty">
          No dining locations have been loaded yet.
        </StateMessage>
      ) : (
        <div className="menus-layout">
          <nav
            ref={pickerRef}
            className="location-picker"
            aria-label="Dining locations"
          >
            {groups.map((group) => (
              <div key={group.title} className="picker-group">
                <p className="picker-heading">
                  {group.title}{" "}
                  <span className="count">({group.list.length})</span>
                </p>
                <ul>
                  {group.list.map((location) => (
                    <li key={location.id}>
                      <button
                        type="button"
                        className="picker-item"
                        aria-pressed={location.id === selected.id}
                        onClick={() => setChosenId(location.id)}
                      >
                        <span
                          className={`picker-dot ${
                            location.is_open === true
                              ? "is-open"
                              : location.is_open === false
                                ? "is-closed"
                                : ""
                          }`}
                          aria-hidden="true"
                        />
                        <span className="picker-text">
                          <span className="picker-name">{location.name}</span>
                          <span className="picker-when">
                            {shortWhen(location)}
                          </span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </nav>

          <MenuPane
            key={selected.id}
            location={selected}
            profile={profile}
            hideConflicts={hideConflicts}
          />
        </div>
      )}
    </>
  );
}

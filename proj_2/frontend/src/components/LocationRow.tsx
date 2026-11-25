"use client";

import Link from "next/link";
import { formatDuration, minutesUntil, useNow } from "@/lib/clock";
import { formatHours, formatTime } from "@/lib/format";
import type { LocationSummary } from "@/lib/types";
import { StatusPill } from "./Badges";
import { HoursTimeline } from "./HoursTimeline";
import { Icon } from "./Icon";

// Under this many minutes to closing, the card says so.
const CLOSING_SOON = 60;

function timing(location: LocationSummary): string | null {
  if (location.is_open === true && location.closes_at) {
    return `Closes at ${formatTime(location.closes_at)}`;
  }
  if (location.is_open === false) {
    return location.opens_next_at
      ? `Opens again at ${formatTime(location.opens_next_at)}`
      : "Not open again today";
  }
  return null;
}

// One location on the What's Open Now page. `showStatus` is off where the
// section heading already says it (for example "Hours unknown").
export function LocationRow({
  location,
  showStatus = true,
}: {
  location: LocationSummary;
  showStatus?: boolean;
}) {
  const now = useNow();
  const when = timing(location);
  const left =
    now !== null && location.is_open === true && location.closes_at
      ? minutesUntil(location.closes_at, now)
      : null;
  const soon = left !== null && left <= CLOSING_SOON ? left : null;
  const tone =
    location.is_open === true
      ? "location-card is-open"
      : location.is_open === false
        ? "location-card is-closed"
        : "location-card";

  return (
    <li className={`panel ${tone}`}>
      <div className="location-row-head">
        <span className="location-name">{location.name}</span>
        {showStatus ? <StatusPill isOpen={location.is_open} /> : null}
      </div>
      {soon !== null ? (
        <p className="closing-soon">
          <Icon name="clock" size={16} /> Closes in {formatDuration(soon)}
        </p>
      ) : null}
      <HoursTimeline day={location.today} />
      <p className="location-when">
        {when ? <strong>{when}</strong> : null}
        {when ? " · " : ""}
        Today: {formatHours(location.today)}
      </p>
      {location.description ? (
        <p className="meta location-desc">{location.description}</p>
      ) : null}
      <div className="row-actions">
        <Link href={`/menus?location=${location.id}`} className="btn btn-small">
          View menu <Icon name="arrow" size={16} />
        </Link>
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
    </li>
  );
}

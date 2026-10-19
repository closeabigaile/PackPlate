import Link from "next/link";
import { formatHours, formatTime } from "@/lib/format";
import type { LocationSummary } from "@/lib/types";
import { StatusPill } from "./Badges";

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

// One location in the What's Open Now lists.
export function LocationRow({ location }: { location: LocationSummary }) {
  const when = timing(location);

  return (
    <li className="panel location-row">
      <div className="location-row-head">
        <span className="location-name">{location.name}</span>
        <StatusPill isOpen={location.is_open} />
      </div>
      <p className="meta">
        Today: {formatHours(location.today)}
        {when ? ` · ${when}` : ""}
      </p>
      {location.description ? <p className="meta">{location.description}</p> : null}
      <div className="row-links">
        <Link href={`/menus?location=${location.id}`}>View menu</Link>
        {location.dining_url ? (
          <a href={location.dining_url} target="_blank" rel="noopener noreferrer">
            Dining page (opens in a new tab)
          </a>
        ) : null}
      </div>
    </li>
  );
}

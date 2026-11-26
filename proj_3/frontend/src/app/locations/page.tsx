"use client";

// What's Open Now: open locations and their hours, closed ones below.
// Backed by GET /locations.
import { useState } from "react";
import { LocationRow } from "@/components/LocationRow";
import { PageShell } from "@/components/PageShell";
import { StateMessage } from "@/components/StateMessage";
import { api } from "@/lib/api";
import { locationKind, type LocationKind } from "@/lib/locationKind";
import type { LocationSummary } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";

type KindFilter = "all" | LocationKind;

const KINDS: { value: KindFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "hall", label: "Dining halls" },
  { value: "other", label: "Cafés and food courts" },
];

// Open ones closing soonest first: that's the one to hurry to.
function byClosing(a: LocationSummary, b: LocationSummary): number {
  if (a.closes_at && b.closes_at) return a.closes_at.localeCompare(b.closes_at);
  return a.closes_at ? -1 : b.closes_at ? 1 : a.name.localeCompare(b.name);
}

export default function LocationsPage() {
  const { data, error, loading, reload } = useAsync(api.locations, "locations");
  const [kind, setKind] = useState<KindFilter>("all");
  const [openOnly, setOpenOnly] = useState(false);

  const shown =
    data?.filter((l) => kind === "all" || locationKind(l) === kind) ?? [];
  const open = shown.filter((l) => l.is_open === true).sort(byClosing);
  const closed = shown.filter((l) => l.is_open === false);
  const unknown = shown.filter((l) => l.is_open === null);

  return (
    <PageShell
      title="What’s open now"
      icon="clock"
      lede="Every dining location, with today’s hours."
    >
      {error ? (
        <StateMessage kind="error" onRetry={reload}>
          {error}
        </StateMessage>
      ) : loading && !data ? (
        <StateMessage kind="loading">Loading locations…</StateMessage>
      ) : data && data.length === 0 ? (
        <StateMessage kind="empty">
          No dining locations have been loaded yet.
        </StateMessage>
      ) : (
        <>
          <div className="filter-bar" role="group" aria-label="Filter">
            <div className="segmented" role="group" aria-label="Kind of place">
              {KINDS.map((k) => (
                <button
                  key={k.value}
                  type="button"
                  className="segment"
                  aria-pressed={kind === k.value}
                  onClick={() => setKind(k.value)}
                >
                  {k.label}
                </button>
              ))}
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={openOnly}
                onChange={(event) => setOpenOnly(event.target.checked)}
              />
              <span className="toggle-track" aria-hidden="true" />
              Open now only
            </label>
          </div>

          <section aria-labelledby="open-title">
            <h2 id="open-title" className="section-title">
              Open now <span className="count">({open.length})</span>
            </h2>
            {open.length === 0 ? (
              <StateMessage kind="empty">
                Nothing {kind === "all" ? "" : "like that "}is open right now.
              </StateMessage>
            ) : (
              <ul className="location-grid">
                {open.map((location) => (
                  <LocationRow
                    key={location.id}
                    location={location}
                    showStatus={false}
                  />
                ))}
              </ul>
            )}
          </section>

          {!openOnly && unknown.length > 0 ? (
            <section aria-labelledby="unknown-title">
              <h2 id="unknown-title" className="section-title">
                Hours unknown <span className="count">({unknown.length})</span>
              </h2>
              <p className="help section-help">
                We couldn’t get today’s hours for these. Check the dining page
                before you go.
              </p>
              <ul className="location-grid">
                {unknown.map((location) => (
                  <LocationRow
                    key={location.id}
                    location={location}
                    showStatus={false}
                  />
                ))}
              </ul>
            </section>
          ) : null}

          {!openOnly ? (
            <section aria-labelledby="closed-title">
              <h2 id="closed-title" className="section-title">
                Closed <span className="count">({closed.length})</span>
              </h2>
              {closed.length === 0 ? (
                <StateMessage kind="empty">
                  Nothing is closed right now.
                </StateMessage>
              ) : (
                <ul className="location-grid">
                  {closed.map((location) => (
                    <LocationRow
                      key={location.id}
                      location={location}
                      showStatus={false}
                    />
                  ))}
                </ul>
              )}
            </section>
          ) : null}
        </>
      )}
    </PageShell>
  );
}

"use client";

// What's Open Now: open locations and their hours, closed ones below.
// Backed by GET /locations.
import { LocationRow } from "@/components/LocationRow";
import { PageShell } from "@/components/PageShell";
import { StateMessage } from "@/components/StateMessage";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

export default function LocationsPage() {
  const { data, error, loading, reload } = useAsync(api.locations, "locations");

  const open = data?.filter((l) => l.is_open === true) ?? [];
  const closed = data?.filter((l) => l.is_open === false) ?? [];
  const unknown = data?.filter((l) => l.is_open === null) ?? [];

  return (
    <PageShell
      title="What’s Open Now"
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
          <section aria-labelledby="open-title">
            <h2 id="open-title" className="section-title">
              Open now <span className="count">({open.length})</span>
            </h2>
            {open.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is open right now.
              </StateMessage>
            ) : (
              <ul className="stack">
                {open.map((location) => (
                  <LocationRow key={location.id} location={location} />
                ))}
              </ul>
            )}
          </section>

          {unknown.length > 0 ? (
            <section aria-labelledby="unknown-title">
              <h2 id="unknown-title" className="section-title">
                Hours unknown <span className="count">({unknown.length})</span>
              </h2>
              <p className="help" style={{ marginBottom: "0.6rem" }}>
                We couldn’t get today’s hours for these. Check the dining page
                before you go.
              </p>
              <ul className="stack">
                {unknown.map((location) => (
                  <LocationRow key={location.id} location={location} />
                ))}
              </ul>
            </section>
          ) : null}

          <section aria-labelledby="closed-title">
            <h2 id="closed-title" className="section-title">
              Closed <span className="count">({closed.length})</span>
            </h2>
            {closed.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is closed right now.
              </StateMessage>
            ) : (
              <ul className="stack">
                {closed.map((location) => (
                  <LocationRow key={location.id} location={location} />
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </PageShell>
  );
}

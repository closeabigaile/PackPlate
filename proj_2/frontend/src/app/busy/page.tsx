"use client";

// How Busy Is It?: crowd levels at open locations, and a way to report.
// Backed by `crowd` in GET /locations and POST /crowd/{id}.
import { useState } from "react";
import { CrowdBadge, StatusPill } from "@/components/Badges";
import { PageShell } from "@/components/PageShell";
import { StateMessage } from "@/components/StateMessage";
import { api, ApiError, errorMessage } from "@/lib/api";
import { CROWD_LABELS } from "@/lib/diet";
import { formatTime } from "@/lib/format";
import type { Crowd, CrowdLevel, LocationSummary } from "@/lib/types";
import { useAsync } from "@/lib/useAsync";

const LEVELS: CrowdLevel[] = ["not_busy", "moderate", "crowded"];

interface Notice {
  tone: "ok" | "bad";
  text: string;
}

export default function BusyPage() {
  const { data, error, reload } = useAsync(api.locations, "locations");
  // Crowd levels returned by reports made on this page, newer than `data`.
  const [updated, setUpdated] = useState<Record<number, Crowd>>({});
  const [notices, setNotices] = useState<Record<number, Notice>>({});
  const [pending, setPending] = useState<number | null>(null);

  async function report(location: LocationSummary, level: CrowdLevel) {
    setPending(location.id);
    try {
      const crowd = await api.reportCrowd(location.id, level);
      setUpdated((prev) => ({ ...prev, [location.id]: crowd }));
      setNotices((prev) => ({
        ...prev,
        [location.id]: {
          tone: "ok",
          text: `Thanks! You reported ${location.name} as ${CROWD_LABELS[level].toLowerCase()}.`,
        },
      }));
    } catch (failure) {
      const text =
        failure instanceof ApiError && failure.status === 429
          ? `You already reported ${location.name} a moment ago.${
              failure.retryAfterSeconds
                ? ` Try again in about ${failure.retryAfterSeconds} seconds.`
                : ""
            }`
          : errorMessage(failure);
      setNotices((prev) => ({ ...prev, [location.id]: { tone: "bad", text } }));
    } finally {
      setPending(null);
    }
  }

  const crowdOf = (location: LocationSummary): Crowd =>
    updated[location.id] ?? location.crowd;

  const reportable = data?.filter((l) => l.is_open !== false) ?? [];
  const closed = data?.filter((l) => l.is_open === false) ?? [];

  return (
    <PageShell
      title="How Busy Is It?"
      lede="Crowd levels at open locations, from reports by students in the last 30 minutes. Newer reports count more."
    >
      {error ? (
        <StateMessage kind="error" onRetry={reload}>
          {error}
        </StateMessage>
      ) : !data ? (
        <StateMessage kind="loading">Loading crowd levels…</StateMessage>
      ) : (
        <>
          <p className="help">
            “No recent reports” means we don’t know, not that it’s empty. Been
            somewhere? Report it to help the next person.
          </p>

          <section aria-labelledby="busy-open-title">
            <h2 id="busy-open-title" className="section-title">
              Open now <span className="count">({reportable.length})</span>
            </h2>
            {reportable.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is open right now.
              </StateMessage>
            ) : (
              <ul className="stack">
                {reportable.map((location) => {
                  const crowd = crowdOf(location);
                  const notice = notices[location.id];
                  return (
                    <li key={location.id} className="panel location-row">
                      <div className="location-row-head">
                        <span className="location-name">{location.name}</span>
                        <StatusPill isOpen={location.is_open} />
                      </div>
                      <p>
                        <CrowdBadge crowd={crowd} />
                        {crowd.last_reported_at ? (
                          <span className="meta">
                            {" "}
                            Last report at {formatTime(crowd.last_reported_at)}
                          </span>
                        ) : null}
                      </p>

                      <div
                        className="crowd-actions"
                        role="group"
                        aria-label={`Report how busy ${location.name} is`}
                      >
                        <span className="meta">Right now it’s:</span>
                        {LEVELS.map((level) => (
                          <button
                            key={level}
                            type="button"
                            className="crowd-btn"
                            disabled={pending !== null}
                            onClick={() => report(location, level)}
                            aria-label={`Report ${location.name} as ${CROWD_LABELS[level]}`}
                          >
                            {CROWD_LABELS[level]}
                          </button>
                        ))}
                      </div>

                      {notice ? (
                        <p
                          className={
                            notice.tone === "ok"
                              ? "banner banner-ok"
                              : "banner banner-bad"
                          }
                          role="status"
                        >
                          {notice.text}
                        </p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </section>

          {closed.length > 0 ? (
            <section aria-labelledby="busy-closed-title">
              <h2 id="busy-closed-title" className="section-title">
                Closed right now{" "}
                <span className="count">({closed.length})</span>
              </h2>
              <ul className="stack">
                {closed.map((location) => (
                  <li key={location.id} className="panel location-row">
                    <div className="location-row-head">
                      <span className="location-name">{location.name}</span>
                      <StatusPill isOpen={false} />
                    </div>
                    <p className="meta">
                      Crowd reports are for open locations.
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </>
      )}
    </PageShell>
  );
}

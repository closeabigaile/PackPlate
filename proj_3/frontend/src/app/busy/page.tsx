"use client";

// How Busy Is It?: crowd levels at open locations, and a way to report.
// Backed by `crowd` in GET /locations and POST /crowd/{id}.
import { useState } from "react";
import { StatusPill } from "@/components/Badges";
import { CrowdMeter } from "@/components/CrowdMeter";
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

function reportsText(count: number): string {
  return `${count} report${count === 1 ? "" : "s"}`;
}

// What the meter shows: the forecast blended with recent reports, or, right
// after you report, the fresh level from reports alone. Always says which.
function meterFor(
  location: LocationSummary,
  crowd: Crowd,
): { level: CrowdLevel | null; basis: string } {
  if (crowd !== location.crowd) {
    return { level: crowd.level, basis: reportsText(crowd.report_count) };
  }
  const { estimate, source } = location.forecast;
  if (estimate !== null && source !== "none") {
    return {
      level: estimate,
      basis:
        source === "reports"
          ? reportsText(crowd.report_count)
          : source === "forecast+reports"
            ? `predicted + ${reportsText(crowd.report_count)}`
            : "predicted, no reports yet",
    };
  }
  return crowd.level !== null
    ? { level: crowd.level, basis: reportsText(crowd.report_count) }
    : { level: null, basis: "no recent reports" };
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

  // Unknown hours can still be reported (you may be standing there), but they
  // are listed apart from "Open now" so this page agrees with What's open.
  const open = data?.filter((l) => l.is_open === true) ?? [];
  const unknown = data?.filter((l) => l.is_open === null) ?? [];
  const closed = data?.filter((l) => l.is_open === false) ?? [];

  function renderReportable(list: LocationSummary[], showStatus: boolean) {
    return (
      <ul className="stack">
        {list.map((location) => {
          const crowd = crowdOf(location);
          const notice = notices[location.id];
          return (
            <li key={location.id} className="panel busy-card">
              <div className="location-row-head">
                <span className="location-name">{location.name}</span>
                {showStatus ? <StatusPill isOpen={location.is_open} /> : null}
              </div>
              <div className="busy-levels">
                <CrowdMeter {...meterFor(location, crowd)} />
                {crowd.last_reported_at ? (
                  <span className="meta">
                    Last report at {formatTime(crowd.last_reported_at)}
                  </span>
                ) : null}
              </div>

              <div className="crowd-report">
                <span className="meta" id={`report-${location.id}`}>
                  Here now? It’s:
                </span>
                <div
                  className="segmented"
                  role="group"
                  aria-labelledby={`report-${location.id}`}
                >
                  {LEVELS.map((level) => (
                    <button
                      key={level}
                      type="button"
                      className={`segment segment-${level}`}
                      disabled={pending !== null}
                      onClick={() => report(location, level)}
                      aria-label={`Report ${location.name} as ${CROWD_LABELS[level]}`}
                    >
                      <span className="segment-dot" aria-hidden="true" />
                      {CROWD_LABELS[level]}
                    </button>
                  ))}
                </div>
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
    );
  }

  return (
    <PageShell
      title="How busy is it?"
      icon="activity"
      lede="Crowd levels from student reports in the last 30 minutes (newer ones count more), plus a forecast when nobody has reported."
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
              Open now <span className="count">({open.length})</span>
            </h2>
            {open.length === 0 ? (
              <StateMessage kind="empty">
                Nothing is confirmed open right now.
              </StateMessage>
            ) : (
              renderReportable(open, false)
            )}
          </section>

          {unknown.length > 0 ? (
            <section aria-labelledby="busy-unknown-title">
              <h2 id="busy-unknown-title" className="section-title">
                Hours unknown <span className="count">({unknown.length})</span>
              </h2>
              <p className="help section-help">
                We couldn’t get today’s hours for these. If you’re there, you
                can still report how busy it is.
              </p>
              {renderReportable(unknown, false)}
            </section>
          ) : null}

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

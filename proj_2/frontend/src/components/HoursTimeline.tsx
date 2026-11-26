"use client";

import type { CSSProperties } from "react";
import { campusMinutes, useNow } from "@/lib/clock";
import type { HoursDay } from "@/lib/types";

// Today's opening hours as a bar from 6 am to midnight, with a line at now.
// Purely visual: the same hours are written out next to it in words.
const START = 6 * 60;
const END = 24 * 60;
const SPAN = END - START;

function pct(minutes: number): number {
  return (Math.min(Math.max(minutes, START), END) - START) / SPAN;
}

export function HoursTimeline({ day }: { day: HoursDay }) {
  const now = useNow();
  if (day.status === "unknown") return null;

  const segments = day.periods.map((p) => {
    const open = campusMinutes(p.opens_at);
    let close = campusMinutes(p.closes_at);
    // Closing at or after midnight: draw to the end of the bar.
    if (close <= open) close = END;
    return { start: pct(open), end: pct(close) };
  });

  // Only today's line: the summary is for the campus date it describes.
  const nowMinutes = now === null ? null : campusMinutes(now);
  const showNow =
    nowMinutes !== null && nowMinutes >= START && nowMinutes <= END;

  return (
    <div className="timeline" aria-hidden="true">
      <div className="timeline-track">
        {segments.map((s, i) => (
          <span
            key={i}
            className="timeline-open"
            style={
              {
                "--from": `${s.start * 100}%`,
                "--to": `${(1 - s.end) * 100}%`,
              } as CSSProperties
            }
          />
        ))}
        {showNow ? (
          <span
            className="timeline-now"
            style={{ left: `${pct(nowMinutes) * 100}%` }}
          />
        ) : null}
      </div>
      <div className="timeline-ticks">
        <span>6a</span>
        <span>12p</span>
        <span>6p</span>
        <span>12a</span>
      </div>
    </div>
  );
}

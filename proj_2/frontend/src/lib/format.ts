import type { HoursDay } from "./types";

const CAMPUS_TZ = "America/New_York";

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: CAMPUS_TZ,
  });
}

// "2026-10-12" -> "Mon, Oct 12". Built from the date parts so the viewer's
// time zone can never shift the day.
export function formatDay(ymd: string): string {
  const [year, month, day] = ymd.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day)).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

// Today's hours as the dining site shows them, else built from the periods.
export function formatHours(day: HoursDay): string {
  if (day.status === "unknown") return "Hours not available";
  if (day.status === "closed" || day.periods.length === 0) {
    return day.raw_text ?? "Closed today";
  }
  return day.periods
    .map((p) => `${formatTime(p.opens_at)} – ${formatTime(p.closes_at)}`)
    .join(", ");
}

export function formatAge(hours: number): string {
  if (hours < 1) return "less than an hour ago";
  if (hours < 48) {
    const h = Math.floor(hours);
    return `${h} hour${h === 1 ? "" : "s"} ago`;
  }
  return `${Math.floor(hours / 24)} days ago`;
}

export function formatNumber(value: number | null, unit: string): string {
  if (value === null) return "not listed";
  return `${Math.round(value * 10) / 10}${unit}`;
}

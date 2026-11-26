"use client";

import { useSyncExternalStore } from "react";
import { nowMs } from "./now";

// The current time for things like "closes in 20 min" and the "now" line on an
// hours bar. Read from a store that ticks every 30 seconds, so reading the
// clock is never part of rendering. Null until the page is in the browser.

const TICK_MS = 30_000;
let now = nowMs();
const listeners = new Set<() => void>();
let timer: ReturnType<typeof setInterval> | null = null;

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (timer === null) {
    now = nowMs();
    timer = setInterval(() => {
      now = nowMs();
      listeners.forEach((l) => l());
    }, TICK_MS);
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0 && timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  };
}

export function useNow(): number | null {
  return useSyncExternalStore(
    subscribe,
    () => now,
    () => null,
  );
}

const PARTS = new Intl.DateTimeFormat("en-US", {
  timeZone: "America/New_York",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

// Minutes after midnight, campus time (0–1439).
export function campusMinutes(time: string | number): number {
  const parts = PARTS.formatToParts(new Date(time));
  const get = (type: string) =>
    Number(parts.find((p) => p.type === type)?.value ?? 0);
  return get("hour") * 60 + get("minute");
}

// "45 min" / "1 h 20 min" until `iso`, or null if it's past.
export function minutesUntil(iso: string, nowMs: number): number | null {
  const diff = Math.round((new Date(iso).getTime() - nowMs) / 60_000);
  return diff >= 0 ? diff : null;
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h} h` : `${h} h ${m} min`;
}

"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useAsync } from "@/lib/useAsync";

// A live line under the Home hero: how many locations are open right now.
// Says nothing rather than guess while loading or if the API is down.
export function OpenNowStrip() {
  const { data } = useAsync(api.locations, "locations");
  if (!data || data.length === 0) return null;

  const open = data.filter((l) => l.is_open === true).length;
  const unknown = data.filter((l) => l.is_open === null).length;

  return (
    <p className="hero-live" role="status">
      <span
        className={open > 0 ? "live-dot live-dot-on" : "live-dot"}
        aria-hidden="true"
      />
      {open > 0
        ? `${open} of ${data.length} dining locations open right now`
        : unknown > 0
          ? `Nothing confirmed open right now (${unknown} with unknown hours)`
          : "Nothing is open right now"}
      <Link href="/locations">See which</Link>
    </p>
  );
}

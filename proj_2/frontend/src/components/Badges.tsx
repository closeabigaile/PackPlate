import { CROWD_LABELS } from "@/lib/diet";
import type { Crowd, Verdict } from "@/lib/types";
import { reasonSummary } from "@/lib/verdicts";

// Meaning is always in the words, never in colour alone.

export function StatusPill({ isOpen }: { isOpen: boolean | null }) {
  if (isOpen === true) return <span className="pill pill-ok">● Open now</span>;
  if (isOpen === false) return <span className="pill">Closed</span>;
  return <span className="pill pill-warn">? Hours unknown</span>;
}

export function CrowdBadge({ crowd }: { crowd: Crowd }) {
  if (crowd.level === null) {
    return <span className="pill">No recent reports</span>;
  }
  const tone =
    crowd.level === "not_busy"
      ? "pill-ok"
      : crowd.level === "moderate"
        ? "pill-warn"
        : "pill-bad";
  const reports = `${crowd.report_count} report${crowd.report_count === 1 ? "" : "s"}`;
  return (
    <span className={`pill ${tone}`}>
      {CROWD_LABELS[crowd.level]} · {reports}
    </span>
  );
}

export function VerdictBadge({
  verdict,
  reasons = [],
}: {
  verdict: Verdict;
  reasons?: string[];
}) {
  if (verdict === "fits") return <span className="pill pill-ok">✓ Fits</span>;
  if (verdict === "conflicts") {
    return <span className="pill pill-bad">✕ Doesn’t fit</span>;
  }
  // Name what's uncertain ("Not labeled Halal"), not a generic "unknown".
  return <span className="pill pill-warn">{reasonSummary(reasons)}</span>;
}

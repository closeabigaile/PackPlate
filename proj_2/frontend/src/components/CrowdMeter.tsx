import { CROWD_LABELS } from "@/lib/diet";
import type { CrowdLevel } from "@/lib/types";

const STEPS: CrowdLevel[] = ["not_busy", "moderate", "crowded"];

// Three steps, filled up to the level. The level is always written out too, so
// colour never carries the meaning alone. `level` null = we don't know.
export function CrowdMeter({
  level,
  basis,
}: {
  level: CrowdLevel | null;
  basis: string;
}) {
  const filled = level === null ? 0 : STEPS.indexOf(level) + 1;
  return (
    <div className={`crowd-meter crowd-${level ?? "unknown"}`}>
      <span className="crowd-steps" aria-hidden="true">
        {STEPS.map((step, i) => (
          <span key={step} className={i < filled ? "step on" : "step"} />
        ))}
      </span>
      <span className="crowd-text">
        <strong>{level === null ? "Unknown" : CROWD_LABELS[level]}</strong>
        <span className="meta"> · {basis}</span>
      </span>
    </div>
  );
}

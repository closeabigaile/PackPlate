import type { ReactNode } from "react";

// One look for "loading", "failed" and "nothing here" across every page.
// Loading shows grey placeholder cards; the words are still read out.
export function StateMessage({
  kind,
  children,
  onRetry,
}: {
  kind: "loading" | "error" | "empty";
  children: ReactNode;
  onRetry?: () => void;
}) {
  if (kind === "loading") {
    return (
      <div className="skeleton-group" role="status">
        <span className="visually-hidden">{children}</span>
        <span className="skeleton" aria-hidden="true" />
        <span className="skeleton" aria-hidden="true" />
        <span className="skeleton skeleton-short" aria-hidden="true" />
      </div>
    );
  }
  return (
    <div
      className={kind === "error" ? "state-message error" : "state-message"}
      role={kind === "error" ? "alert" : "status"}
    >
      <p>{children}</p>
      {kind === "error" && onRetry ? (
        <button type="button" className="btn btn-small" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}

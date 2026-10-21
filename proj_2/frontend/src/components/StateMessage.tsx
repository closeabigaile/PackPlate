import type { ReactNode } from "react";

// One look for "loading", "failed" and "nothing here" across every page.
export function StateMessage({
  kind,
  children,
  onRetry,
}: {
  kind: "loading" | "error" | "empty";
  children: ReactNode;
  onRetry?: () => void;
}) {
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

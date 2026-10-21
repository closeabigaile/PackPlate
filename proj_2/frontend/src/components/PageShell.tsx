import type { ReactNode } from "react";
import { FreshnessBanner } from "./FreshnessBanner";

export function PageShell({
  title,
  lede,
  children,
  showFreshness = true,
}: {
  title: string;
  lede?: string;
  children: ReactNode;
  showFreshness?: boolean;
}) {
  return (
    <main className="page">
      <h1 className="page-title">{title}</h1>
      {lede ? <p className="page-lede">{lede}</p> : null}
      {showFreshness ? <FreshnessBanner /> : null}
      <div className="page-body">{children}</div>
    </main>
  );
}

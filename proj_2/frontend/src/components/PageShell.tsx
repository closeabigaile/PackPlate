import type { ReactNode } from "react";
import { FreshnessBanner } from "./FreshnessBanner";
import { Icon, type IconName } from "./Icon";

export function PageShell({
  title,
  lede,
  icon,
  children,
  showFreshness = true,
}: {
  title: string;
  lede?: string;
  icon?: IconName;
  children: ReactNode;
  showFreshness?: boolean;
}) {
  return (
    <main className="page">
      <header className="page-head">
        {icon ? (
          <span className="page-icon" aria-hidden="true">
            <Icon name={icon} size={26} />
          </span>
        ) : null}
        <div className="page-head-text">
          <h1 className="page-title">{title}</h1>
          {lede ? <p className="page-lede">{lede}</p> : null}
        </div>
      </header>
      {showFreshness ? <FreshnessBanner /> : null}
      <div className="page-body">{children}</div>
    </main>
  );
}

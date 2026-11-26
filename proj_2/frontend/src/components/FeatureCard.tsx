import Link from "next/link";
import type { CSSProperties } from "react";
import { Icon, type IconName } from "./Icon";

// One feature on the Home page: an icon, what it is, and what it's for. The
// whole card is the link.
export function FeatureCard({
  href,
  title,
  description,
  icon,
  accent,
  tag,
}: {
  href: string;
  title: string;
  description: string;
  icon: IconName;
  accent: string;
  tag?: string;
}) {
  return (
    <Link
      href={href}
      className="feature-card"
      style={{ "--accent": accent } as CSSProperties}
    >
      <span className="feature-icon" aria-hidden="true">
        <Icon name={icon} size={24} />
      </span>
      <span className="feature-text">
        <span className="feature-title">
          {title}
          {tag ? <span className="feature-tag">{tag}</span> : null}
        </span>
        <span className="feature-desc">{description}</span>
      </span>
      <Icon name="arrow" size={18} className="feature-arrow" />
    </Link>
  );
}

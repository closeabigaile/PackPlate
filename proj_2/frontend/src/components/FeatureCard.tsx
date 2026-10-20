import Link from "next/link";
import type { CSSProperties } from "react";

// One of the five cards on the Home page: art on top, a coloured label with a
// button at the bottom, like the NC State Dining cards the wireframe borrows.
// Swap the emoji for an <Image> when real photos are available.
export function FeatureCard({
  href,
  title,
  action,
  accent,
  art,
}: {
  href: string;
  title: string;
  action: string;
  accent: string;
  art: string;
}) {
  return (
    <article
      className="feature-card"
      style={{ "--accent": accent } as CSSProperties}
    >
      <div className="feature-art" aria-hidden="true">
        {art}
      </div>
      <div className="feature-label">
        <h2>{title}</h2>
        <Link href={href} className="btn">
          {action}
        </Link>
      </div>
    </article>
  );
}

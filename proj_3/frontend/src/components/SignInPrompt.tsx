import Link from "next/link";
import { Icon, type IconName } from "./Icon";

// Shown in place of a feature that needs an account: what it does, then the
// way in. Better than an empty page with one line.
export function SignInPrompt({
  icon,
  title,
  points,
  examples,
}: {
  icon: IconName;
  title: string;
  points: string[];
  examples?: string[];
}) {
  return (
    <section className="signin-prompt" aria-labelledby="signin-title">
      <div className="signin-main">
        <span className="page-icon" aria-hidden="true">
          <Icon name={icon} size={26} />
        </span>
        <h2 id="signin-title">{title}</h2>
        <ul className="signin-points">
          {points.map((point) => (
            <li key={point}>
              <Icon name="check" size={18} />
              {point}
            </li>
          ))}
        </ul>
        <div className="button-row">
          <Link href="/signup" className="btn">
            Create an account
          </Link>
          <Link href="/login" className="btn btn-quiet">
            <Icon name="lock" size={16} /> Log in
          </Link>
        </div>
        <p className="help">
          You only need a username and a password. No email.
        </p>
      </div>
      {examples && examples.length > 0 ? (
        <div className="signin-examples" aria-label="Examples">
          <p className="eyebrow">Try asking</p>
          <ul>
            {examples.map((text) => (
              <li key={text} className="example-bubble">
                {text}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

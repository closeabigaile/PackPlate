"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";

// Login / Signup screen from the wireframe.
//
// The backend has no accounts yet (docs/m4-web-app.md, "For the team to
// decide"), so this form deliberately sends and stores nothing: submitting only
// shows a notice. When accounts exist, replace onSubmit with a real call.
export function AuthForm({ mode }: { mode: "login" | "signup" }) {
  const [submitted, setSubmitted] = useState(false);
  const isSignup = mode === "signup";

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="panel auth-card stack" role="status">
        <p className="banner banner-warn">
          <strong>Accounts aren’t available yet.</strong> Nothing you typed was
          sent or saved.
        </p>
        <p>
          PackPlate works without one. Your dietary profile stays in this
          browser, so you can use everything right away.
        </p>
        <Link href="/home" className="btn">
          Continue without an account
        </Link>
      </div>
    );
  }

  return (
    <form className="panel auth-card form" onSubmit={onSubmit}>
      <div className="field">
        <label htmlFor="auth-email">NC State email</label>
        <input
          id="auth-email"
          className="input"
          type="email"
          autoComplete="email"
          required
        />
      </div>
      <div className="field">
        <label htmlFor="auth-password">Password</label>
        <input
          id="auth-password"
          className="input"
          type="password"
          autoComplete={isSignup ? "new-password" : "current-password"}
          minLength={8}
          required
        />
      </div>
      <button type="submit" className="btn">
        {isSignup ? "Sign up" : "Log in"}
      </button>
    </form>
  );
}

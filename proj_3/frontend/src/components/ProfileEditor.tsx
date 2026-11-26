"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import {
  clearMyProfile,
  saveMyProfile,
  useProfileSync,
  type SaveOutcome,
} from "@/lib/accountProfile";
import { emptyProfile, validateProfile } from "@/lib/diet";
import { useHydrated, useSavedProfile } from "@/lib/profileStore";
import { useSession } from "@/lib/session";
import type { Profile } from "@/lib/types";
import { DietPreview } from "./DietPreview";
import { ProfileFields } from "./ProfileFields";
import { StateMessage } from "./StateMessage";

type Status =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "cleared" }
  | { kind: "clear_failed"; message: string }
  | SaveOutcome;

function ProfileForm({
  initial,
  username,
  syncProblem,
}: {
  initial: Profile;
  username: string | null; // null when logged out
  syncProblem: string | null;
}) {
  const [draft, setDraft] = useState<Profile>(initial);
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [problem, setProblem] = useState<string | null>(null);
  const busy = status.kind === "saving";

  function update(next: Profile) {
    setDraft(next);
    setStatus({ kind: "idle" });
    setProblem(null);
  }

  async function onSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const invalid = validateProfile(draft);
    if (invalid) {
      setProblem(invalid);
      return;
    }
    setStatus({ kind: "saving" });
    setStatus(
      await saveMyProfile({ ...draft, name: draft.name?.trim() ?? "" }),
    );
  }

  async function onClear() {
    setStatus({ kind: "saving" });
    const failed = await clearMyProfile();
    if (failed) {
      setStatus({ kind: "clear_failed", message: failed });
      return;
    }
    setDraft(emptyProfile());
    setProblem(null);
    setStatus({ kind: "cleared" });
  }

  return (
    <>
      <form className="panel form" onSubmit={onSave}>
        <ProfileFields idPrefix="me" value={draft} onChange={update} showName />

        {syncProblem ? (
          <p className="banner banner-bad" role="alert">
            Couldn’t load the profile saved to your account ({syncProblem}).
            This is the copy in this browser.
          </p>
        ) : null}

        {problem ? (
          <p className="form-error" role="alert">
            {problem}
          </p>
        ) : null}

        <div className="button-row">
          <button type="submit" className="btn" disabled={busy}>
            {busy ? "Saving…" : "Save my profile"}
          </button>
          <button
            type="button"
            className="btn btn-quiet"
            onClick={onClear}
            disabled={busy}
          >
            Clear profile
          </button>
        </div>

        {status.kind === "account" || status.kind === "browser" ? (
          <p className="banner banner-ok" role="status">
            {status.kind === "account"
              ? "Saved to your account. "
              : "Saved in this browser. "}
            <Link href="/menus">See menus for you</Link>
            {", "}
            <Link href="/compare">compare meals</Link>
            {" or "}
            <Link href="/group">eat as a group</Link>.
          </p>
        ) : null}
        {status.kind === "cleared" ? (
          <p className="banner" role="status">
            {username
              ? "Your profile was cleared from your account and this browser."
              : "Your profile was cleared from this browser."}
          </p>
        ) : null}
        {status.kind === "blocked" ? (
          <p className="banner banner-bad" role="alert">
            Your browser wouldn’t let PackPlate save this (private browsing can
            do that). You can still use it on the Group page for this visit, or{" "}
            <Link href="/login">log in</Link> to save it to an account.
          </p>
        ) : null}
        {status.kind === "account_failed" || status.kind === "clear_failed" ? (
          <p className="banner banner-bad" role="alert">
            Couldn’t {status.kind === "account_failed" ? "save" : "clear"} your
            profile on your account: {status.message} Nothing was changed.
          </p>
        ) : null}
      </form>

      <DietPreview profile={draft} />

      <section className="panel" aria-labelledby="privacy-title">
        <h2 id="privacy-title" className="section-title">
          Where is this kept?
        </h2>
        {username ? (
          <p className="help">
            On your account, <strong>{username}</strong>, so it’s there when you
            log in on any device, and in this browser while you’re logged in.
            Logging out removes it from this browser; deleting your account
            deletes it.
          </p>
        ) : (
          <p className="help">
            Only in this browser on this device. It’s sent along when you check
            a menu so the check can be done, and then it’s forgotten.{" "}
            <Link href="/login">Log in</Link> or{" "}
            <Link href="/signup">create an account</Link> to keep it on your
            account and use it on any device.
          </p>
        )}
      </section>
    </>
  );
}

export function ProfileEditor() {
  const hydrated = useHydrated();
  const saved = useSavedProfile();
  const session = useSession();
  const sync = useProfileSync();

  const user = session.status === "signed_in" ? session.user : null;
  // Wait for the browser, and for the account's copy when logged in, so the
  // form starts from what is actually saved.
  const waiting =
    !hydrated ||
    session.status === "loading" ||
    (user !== null &&
      (sync.status === "idle" ||
        sync.status === "syncing" ||
        sync.userId !== user.id));
  if (waiting)
    return <StateMessage kind="loading">Loading your profile…</StateMessage>;

  return (
    <ProfileForm
      // Start over if the account changes while the page is open.
      key={user?.id ?? "browser"}
      initial={saved}
      username={user?.username ?? null}
      syncProblem={sync.status === "failed" ? sync.message : null}
    />
  );
}

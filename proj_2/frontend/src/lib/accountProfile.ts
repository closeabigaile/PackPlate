"use client";

// Keeps the browser's dietary profile (lib/profileStore.ts) and the logged-in
// account's saved profile (GET/PUT/DELETE /profile) the same.
//
//   - Logging in: the account's profile replaces the browser's. If the account
//     has none yet, a profile made while logged out is saved to it.
//   - Saving or clearing on My diet while logged in updates both.
//   - Logging out (here or in another tab) clears it from this browser.
//
// Pages keep reading useSavedProfile(), so they don't need to know about this.
import { useEffect, useRef, useSyncExternalStore } from "react";
import { api, errorMessage } from "./api";
import { hasConstraints, toRequestProfile } from "./diet";
import {
  clearProfile,
  profileOwner,
  readSavedProfile,
  saveProfile,
  setProfileOwner,
} from "./profileStore";
import { getSession, useSession } from "./session";
import type { Profile } from "./types";

export type SyncState =
  | { status: "idle" } // logged out, or not synced yet
  | { status: "syncing"; userId: number }
  | { status: "synced"; userId: number }
  | { status: "failed"; userId: number; message: string };

const IDLE: SyncState = { status: "idle" };
let state: SyncState = IDLE;
const listeners = new Set<() => void>();

function setState(next: SyncState) {
  state = next;
  listeners.forEach((listener) => listener());
}

function stillSignedIn(userId: number): boolean {
  const session = getSession();
  return session.status === "signed_in" && session.user.id === userId;
}

function keepLocally(profile: Profile, userId: number) {
  saveProfile(profile);
  setProfileOwner(userId);
}

async function syncWithAccount(userId: number) {
  if (
    (state.status === "syncing" || state.status === "synced") &&
    state.userId === userId
  )
    return; // already done; a failed sync is retried
  setState({ status: "syncing", userId });
  try {
    const saved = await api.savedProfile();
    if (!stillSignedIn(userId)) return;
    const owner = profileOwner();
    if (saved) {
      keepLocally(saved, userId);
    } else if (owner === null) {
      // Made while logged out: keep it with the new account.
      const local = readSavedProfile();
      if (hasConstraints(local))
        keepLocally(await api.saveProfile(toRequestProfile(local)), userId);
    } else {
      // From this or another account, and not on this account any more.
      clearProfile();
    }
    if (stillSignedIn(userId)) setState({ status: "synced", userId });
  } catch (failure) {
    if (stillSignedIn(userId))
      setState({ status: "failed", userId, message: errorMessage(failure) });
  }
}

// Mounted once in the layout: syncs on login, clears on logout.
export function ProfileSync() {
  const session = useSession();
  const lastUser = useRef<number | null>(null);
  const userId = session.status === "signed_in" ? session.user.id : null;

  useEffect(() => {
    if (userId !== null) {
      lastUser.current = userId;
      void syncWithAccount(userId);
    } else if (session.status === "signed_out") {
      // Only after a real logout: a visitor who never logged in keeps theirs.
      if (lastUser.current !== null) clearProfile();
      lastUser.current = null;
      setState(IDLE);
    }
  }, [userId, session.status]);

  return null;
}

export function useProfileSync(): SyncState {
  return useSyncExternalStore(
    (onChange) => {
      listeners.add(onChange);
      return () => listeners.delete(onChange);
    },
    () => state,
    () => IDLE,
  );
}

export type SaveOutcome =
  | { kind: "account" } // in this browser and on the account
  | { kind: "browser" } // logged out: in this browser only
  | { kind: "blocked" } // logged out and the browser refused
  | { kind: "account_failed"; message: string }; // logged in, the server refused

export async function saveMyProfile(profile: Profile): Promise<SaveOutcome> {
  const session = getSession();
  if (session.status !== "signed_in")
    return saveProfile(profile) ? { kind: "browser" } : { kind: "blocked" };
  try {
    const saved = await api.saveProfile(toRequestProfile(profile));
    keepLocally(saved, session.user.id);
    return { kind: "account" };
  } catch (failure) {
    return { kind: "account_failed", message: errorMessage(failure) };
  }
}

// Returns an error message if the account copy couldn't be removed.
export async function clearMyProfile(): Promise<string | null> {
  const session = getSession();
  if (session.status === "signed_in") {
    try {
      await api.deleteProfile();
    } catch (failure) {
      return errorMessage(failure);
    }
  }
  clearProfile();
  return null;
}

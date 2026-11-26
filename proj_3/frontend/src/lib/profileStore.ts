"use client";

// The dietary profile as this browser has it (localStorage). Every page reads
// it from here. Logged out, this is the only copy. Logged in, lib/accountProfile.ts
// keeps it in sync with the copy saved on the account (GET/PUT /profile), and it
// is cleared from the browser on logout. Filtering still sends the profile in
// the request body.
import { useMemo, useSyncExternalStore } from "react";
import { parseProfile } from "./diet";
import type { Profile } from "./types";

const STORAGE_KEY = "packplate.profile.v1";
// Which account the stored profile came from (a user id), or absent if it was
// made while logged out. Stops one account's profile being saved to another's.
const OWNER_KEY = "packplate.profile.owner";
const listeners = new Set<() => void>();

function read(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null; // storage blocked (private mode, etc.)
  }
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  window.addEventListener("storage", onChange);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

function notify() {
  listeners.forEach((listener) => listener());
}

// Returns false if the browser refused to store it.
export function saveProfile(profile: Profile): boolean {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  } catch {
    return false;
  }
  notify();
  return true;
}

export function clearProfile(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    window.localStorage.removeItem(OWNER_KEY);
  } catch {
    // nothing stored, nothing to clear
  }
  notify();
}

// The saved profile right now, outside React.
export function readSavedProfile(): Profile {
  return parseProfile(read());
}

export function profileOwner(): number | null {
  try {
    const owner = Number(window.localStorage.getItem(OWNER_KEY));
    return Number.isInteger(owner) && owner > 0 ? owner : null;
  } catch {
    return null;
  }
}

export function setProfileOwner(userId: number): void {
  try {
    window.localStorage.setItem(OWNER_KEY, String(userId));
  } catch {
    // storage blocked: the account copy is still saved
  }
}

// true once running in the browser. Forms that start from the saved profile
// wait for this so they never initialise from the empty server-side value.
export function useHydrated(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

export function useSavedProfile(): Profile {
  const raw = useSyncExternalStore(subscribe, read, () => null);
  return useMemo(() => parseProfile(raw), [raw]);
}

"use client";

// Who is logged in, shared by every component (the header, the login pages,
// and any feature that needs an account, like chat). The server holds the
// session in an HttpOnly cookie; this only caches GET /auth/me so the header
// doesn't refetch on every page.
//
//   const session = useSession();
//   if (session.status === "signed_in") session.user.username
import { useSyncExternalStore } from "react";
import { api, ApiError } from "./api";
import type { User } from "./types";

export type Session =
  | { status: "loading" }
  | { status: "signed_out" }
  | { status: "signed_in"; user: User }
  | { status: "unknown" }; // the server couldn't be reached

const LOADING: Session = { status: "loading" };
let current: Session = LOADING;
let started = false;
const listeners = new Set<() => void>();

function set(next: Session) {
  current = next;
  listeners.forEach((listener) => listener());
}

export async function refreshSession(): Promise<Session> {
  try {
    set({ status: "signed_in", user: await api.me() });
  } catch (error) {
    const reachable = error instanceof ApiError && error.status === 401;
    set(reachable ? { status: "signed_out" } : { status: "unknown" });
  }
  return current;
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  if (!started) {
    started = true;
    void refreshSession();
  }
  return () => listeners.delete(onChange);
}

export function useSession(): Session {
  return useSyncExternalStore(
    subscribe,
    () => current,
    () => LOADING,
  );
}

export async function register(username: string, password: string) {
  set({ status: "signed_in", user: await api.register(username, password) });
}

export async function login(username: string, password: string) {
  set({ status: "signed_in", user: await api.login(username, password) });
}

export async function logout() {
  await api.logout();
  set({ status: "signed_out" });
}

export async function setOpenToChat(value: boolean) {
  set({ status: "signed_in", user: await api.setOpenToChat(value) });
}

export async function deleteAccount(password: string) {
  await api.deleteAccount(password);
  set({ status: "signed_out" });
}

// Typed client for the FastAPI backend. Every call the pages make goes through
// here, so a renamed endpoint or field is a type error in one place.
//
// Set NEXT_PUBLIC_API_URL in .env.local to override the local dev server.
import type {
  Crowd,
  CrowdLevel,
  Freshness,
  FilteredMenu,
  GroupLocation,
  LocationDetail,
  LocationSummary,
  Menu,
  Profile,
} from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number; // 0 = the server could not be reached
  retryAfterSeconds: number | null;

  constructor(message: string, status: number, retryAfterSeconds: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

async function request<T>(path: string, body?: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      "Can’t reach the PackPlate server. Check your connection and try again.",
      0,
      null,
    );
  }

  if (!response.ok) {
    let message = `Something went wrong (${response.status}).`;
    try {
      const payload: unknown = await response.json();
      if (
        typeof payload === "object" &&
        payload !== null &&
        "detail" in payload &&
        typeof payload.detail === "string"
      ) {
        message = payload.detail;
      }
    } catch {
      // keep the generic message
    }
    const retryAfter = Number(response.headers.get("Retry-After"));
    throw new ApiError(
      message,
      response.status,
      Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null,
    );
  }
  return (await response.json()) as T;
}

function query(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string] => entry[1] !== undefined,
  );
  if (entries.length === 0) return "";
  return `?${new URLSearchParams(entries).toString()}`;
}

export const api = {
  freshness: () => request<Freshness>("/freshness"),

  locations: () => request<LocationSummary[]>("/locations"),

  location: (id: number) => request<LocationDetail>(`/locations/${id}`),

  menus: (id: number, date?: string) =>
    request<Menu[]>(`/locations/${id}/menus${query({ date })}`),

  // Profiles are sent in the body and are never stored by the server.
  filterMenus: (id: number, profiles: Profile[], date?: string) =>
    request<FilteredMenu[]>(`/filters/locations/${id}/menus${query({ date })}`, {
      profiles,
    }),

  filterGroup: (profiles: Profile[]) =>
    request<GroupLocation[]>("/filters/group", { profiles }),

  reportCrowd: (id: number, level: CrowdLevel) =>
    request<Crowd>(`/crowd/${id}`, { level }),
};

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong.";
}

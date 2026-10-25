import type { ApiErrorBody } from "../types/api";

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

type QueryValue = string | boolean | undefined;

function buildUrl(path: string, query: Record<string, QueryValue>): string {
  const base = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(/\/$/, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  const url = base.startsWith("http")
    ? new URL(`${base}${suffix}`)
    : new URL(`${base}${suffix}`, window.location.origin);
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

function readMessage(body: unknown, fallback: string): { message: string; code?: string } {
  if (body && typeof body === "object" && "error" in body) {
    const error = (body as ApiErrorBody).error;
    if (error?.message) {
      return { message: error.message, code: error.code };
    }
  }
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return { message: detail };
    }
  }
  return { message: fallback };
}

export async function apiGet<T>(path: string, query: Record<string, QueryValue>, signal?: AbortSignal): Promise<T> {
  const response = await fetch(buildUrl(path, query), {
    signal,
    headers: { Accept: "application/json" },
  });
  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text) as unknown;
    } catch {
      body = null;
    }
  }
  if (!response.ok) {
    const parsed = readMessage(body, `Request failed (${response.status})`);
    throw new ApiError(parsed.message, response.status, parsed.code);
  }
  if (body === null) {
    throw new ApiError("The server returned an empty response", response.status);
  }
  return body as T;
}

/**
 * lib/apiClient.ts
 * -------------------
 * SHARED FILE - the one base fetch wrapper everyone's api/*.ts files use.
 * Handles attaching the JWT token and throwing real errors on failed
 * requests. Stable on purpose - you should almost never need to edit
 * this file; add your own logic in your own file under lib/api/ instead.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_token");
}

export function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

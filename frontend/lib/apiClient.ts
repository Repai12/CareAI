/**
 * lib/apiClient.ts
 * -------------------
 * SHARED FILE - the one base fetch wrapper everyone's api/*.ts files use.
 * Handles attaching the JWT token and throwing real errors on failed
 * requests. Stable on purpose - you should almost never need to edit
 * this file; add your own logic in your own file under lib/api/ instead.
 *
 * Session model (README S3.2/3.5): the access token lives in memory only
 * (never localStorage, which is vulnerable to XSS token theft) and is
 * short-lived. It doesn't survive a page reload by itself, so on a 401 -
 * or on the very first request after a reload, when memory is empty -
 * this silently exchanges the httpOnly refresh cookie for a new access
 * token via /auth/refresh instead of bouncing straight to /login. That's
 * what keeps a half-filled vitals form from being lost to a token
 * timeout mid-entry, and what makes an in-memory (not localStorage)
 * token workable across reloads at all.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

export function setToken(token: string | null) {
  accessToken = token;
}

export function getToken(): string | null {
  return accessToken;
}

export function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export function setMyRole(role: string | null) {
  if (typeof window === "undefined") return;
  if (role) localStorage.setItem("careai_role", role);
  else localStorage.removeItem("careai_role");
}

/** Exchanges the httpOnly refresh cookie for a new access token. Coalesces concurrent callers into one request. */
function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) {
          accessToken = null;
          return null;
        }
        const data = await res.json();
        accessToken = data.access_token;
        setMyRole(data.role);
        return accessToken;
      })
      .catch(() => {
        accessToken = null;
        return null;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

/** Clears the in-memory token and revokes the refresh cookie server-side. */
export async function endSession(): Promise<void> {
  accessToken = null;
  setMyRole(null);
  try {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
  } catch {
    // Best-effort - the cookie is cleared client-side by the browser's
    // response handling regardless of whether this network call lands.
  }
}

export async function apiFetch(path: string, options: RequestInit = {}, _hasRetried = false): Promise<any> {
  const isAuthRoute = path.startsWith("/auth/");

  // No token in memory yet (fresh page load) - try to restore the
  // session from the refresh cookie before giving up on a 401.
  if (!accessToken && !isAuthRoute) {
    await refreshAccessToken();
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.headers || {}),
    },
  });

  if (res.status === 401 && !isAuthRoute && !_hasRetried) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiFetch(path, options, true);
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

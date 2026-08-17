/**
 * lib/api/auth.ts
 * ------------------
 * SHARED FILE - login/registration API calls, used by every role.
 */

import { apiFetch } from "@/lib/apiClient";

export interface RegisterResponse {
  id: string;
  email: string;
  role: string;
  patient_code?: string | null;
  link_pending?: boolean;
}

export function login(email: string, password: string) {
  return apiFetch(`/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }) as Promise<{ access_token: string; token_type: string; role: string }>;
}

export function register(payload: {
  name: string;
  email: string;
  password: string;
  role: "patient" | "family" | "doctor";
  patient_code?: string;
}) {
  return apiFetch(`/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<RegisterResponse>;
}

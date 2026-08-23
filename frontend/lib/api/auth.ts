/**
 * lib/api/auth.ts
 * ------------------
 * SHARED FILE - login/registration/session API calls, used by every role.
 */

import { apiFetch, setToken, setMyRole, endSession } from "@/lib/apiClient";

export interface RegisterResponse {
  id: string;
  email: string;
  role: string;
  patient_code?: string | null;
  doctor_unverified_notice?: string | null;
}

interface LoginResult {
  access_token: string;
  token_type: string;
  role: string;
}

export async function login(email: string, password: string): Promise<LoginResult> {
  const res = (await apiFetch(`/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  })) as LoginResult;
  setToken(res.access_token);
  setMyRole(res.role);
  return res;
}

export function register(payload: {
  name: string;
  email: string;
  password: string;
  role: "patient" | "family" | "doctor";
  patient_code?: string;
  license_number?: string;
}) {
  return apiFetch(`/auth/register`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<RegisterResponse>;
}

export function forgotPassword(email: string) {
  return apiFetch(`/auth/forgot-password`, {
    method: "POST",
    body: JSON.stringify({ email }),
  }) as Promise<{ message: string }>;
}

export function resetPassword(token: string, newPassword: string) {
  return apiFetch(`/auth/reset-password/${token}`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  }) as Promise<{ message: string }>;
}

export async function logout(): Promise<void> {
  await endSession();
}

/**
 * api.ts
 * ------
 * Small fetch wrapper so every component doesn't repeat base URL / auth
 * header logic. Reads the JWT from localStorage (set at login).
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_token");
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

// ---- Types matching backend schemas.py ----

export interface VitalsOut {
  id: string;
  blood_pressure: string;
  sugar_level: number;
  heart_rate: number;
  temperature: number;
  recorded_at: string;
}

export interface MedicationOut {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  schedule_time: string;
  active: boolean;
}

export interface AppointmentOut {
  id: string;
  doctor_name: string;
  scheduled_at: string;
  location: string | null;
  status: string;
}

export interface DashboardResponse {
  patient: { id: string; name: string; email: string; role: string };
  latest_vitals: VitalsOut | null;
  active_medications: MedicationOut[];
  upcoming_appointments: AppointmentOut[];
}

export interface WeeklyReportOut {
  id: string;
  patient_id: string;
  sent_to: string;
  summary_text: string;
  status: string;
  sent_at: string;
}

export function getDashboard(patientId: string) {
  return apiFetch(`/dashboard/${patientId}`) as Promise<DashboardResponse>;
}

export function triggerWeeklyReport(patientId: string) {
  return apiFetch(`/reports/weekly/trigger`, {
    method: "POST",
    body: JSON.stringify({ patient_id: patientId }),
  }) as Promise<WeeklyReportOut[]>;
}

export function getReportHistory(patientId: string) {
  return apiFetch(`/reports/weekly/${patientId}`) as Promise<WeeklyReportOut[]>;
}

export function getMyPatients() {
  return apiFetch(`/me/patients`) as Promise<{ id: string; name: string; email: string; role: string }[]>;
}

export function login(email: string, password: string) {
  return apiFetch(`/auth/login`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }) as Promise<{ access_token: string; token_type: string; role: string }>;
}

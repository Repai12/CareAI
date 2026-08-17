/**
 * lib/api/vitals.ts
 * --------------------
 * OWNED BY MEMBER 1 (Mubasshira) - Vitals, AI Report Analyzer, Symptom
 * Checker, Diet Advisor.
 */

import { apiFetch, getToken } from "@/lib/apiClient";
import type { VitalsOut } from "./dashboard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface VitalsEntryOut extends VitalsOut {
  notes: string | null;
  is_abnormal: boolean;
}

export interface VitalsIn {
  blood_pressure: string;
  sugar_level: number;
  heart_rate: number;
  temperature: number;
  notes?: string;
}

export interface HealthReportOut {
  id: string;
  filename: string;
  ai_summary: string | null;
  created_at: string;
}

export interface SymptomLogOut {
  id: string;
  symptoms: string;
  ai_response: string;
  urgency: "normal" | "monitor" | "urgent" | "emergency";
  escalated: boolean;
  created_at: string;
}

export interface DietPlanOut {
  id: string;
  based_on_summary: string;
  ai_plan: string;
  created_at: string;
}

export interface DietLogOut {
  id: string;
  plan_id: string;
  followed: boolean;
  note: string | null;
  logged_at: string;
}

export interface DietPlanWithLogs {
  plan: DietPlanOut | null;
  logs: DietLogOut[];
  adherence_rate: number | null;
}

// --- Feature 1: Vitals CRUD ---

export function logVitals(payload: VitalsIn) {
  return apiFetch(`/vitals`, { method: "POST", body: JSON.stringify(payload) }) as Promise<VitalsEntryOut>;
}

export function getVitalsHistory(patientId: string, limit = 50) {
  return apiFetch(`/vitals/${patientId}/history?limit=${limit}`) as Promise<VitalsEntryOut[]>;
}

export function updateVitals(vitalsId: string, payload: Partial<VitalsIn>) {
  return apiFetch(`/vitals/${vitalsId}`, { method: "PUT", body: JSON.stringify(payload) }) as Promise<VitalsEntryOut>;
}

export function deleteVitals(vitalsId: string) {
  return apiFetch(`/vitals/${vitalsId}`, { method: "DELETE" });
}

// --- Feature 2: AI Health Report Analyzer ---

export async function uploadHealthReport(file: File): Promise<HealthReportOut> {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/vitals/reports/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export function getHealthReports(patientId: string) {
  return apiFetch(`/vitals/${patientId}/reports`) as Promise<HealthReportOut[]>;
}

// --- Feature 3: AI Symptom Checker ---

export function checkSymptoms(symptoms: string) {
  return apiFetch(`/vitals/symptom-check`, {
    method: "POST",
    body: JSON.stringify({ symptoms }),
  }) as Promise<SymptomLogOut>;
}

export function getSymptomLogs(patientId: string) {
  return apiFetch(`/vitals/${patientId}/symptom-logs`) as Promise<SymptomLogOut[]>;
}

// --- Feature 4: AI Diet Advisor ---

export function generateDietPlan() {
  return apiFetch(`/vitals/diet-plan/generate`, { method: "POST" }) as Promise<DietPlanOut>;
}

export function getLatestDietPlan(patientId: string) {
  return apiFetch(`/vitals/${patientId}/diet-plan/latest`) as Promise<DietPlanWithLogs>;
}

export function logDietAdherence(planId: string, followed: boolean, note?: string) {
  return apiFetch(`/vitals/diet-plan/log`, {
    method: "POST",
    body: JSON.stringify({ plan_id: planId, followed, note }),
  }) as Promise<DietLogOut>;
}

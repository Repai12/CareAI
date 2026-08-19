/**
 * lib/api/medicationLogs.ts
 * ----------------------------
 * OWNED BY MEMBER 2 (Afifa) - Medicine Reminder & Adherence Tracker
 * (README S8.4). A "log" is a scheduled dose - create one for a future
 * time, then mark it taken/missed once that time passes.
 */

import { apiFetch } from "@/lib/apiClient";

export interface MedicationLogOut {
  id: string;
  medication_id: string;
  patient_id: string;
  scheduled_at: string;
  taken_at: string | null;
  status: "pending" | "taken" | "missed";
}

export interface AdherenceOut {
  medication_id: string;
  taken: number;
  missed: number;
  pending: number;
  adherence_percentage: number;
}

export function getMedicationLogs(patientId: string, medicationId?: string) {
  const query = medicationId ? `?medication_id=${medicationId}` : "";
  return apiFetch(`/medication-logs/${patientId}${query}`) as Promise<MedicationLogOut[]>;
}

export function scheduleMedicationLog(patientId: string, medicationId: string, scheduledAt: string) {
  return apiFetch(`/medication-logs/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ medication_id: medicationId, scheduled_at: scheduledAt }),
  }) as Promise<MedicationLogOut>;
}

export function markMedicationTaken(patientId: string, logId: string) {
  return apiFetch(`/medication-logs/${patientId}/${logId}/taken`, { method: "PUT" }) as Promise<MedicationLogOut>;
}

export function markMedicationMissed(patientId: string, logId: string) {
  return apiFetch(`/medication-logs/${patientId}/${logId}/missed`, { method: "PUT" }) as Promise<MedicationLogOut>;
}

export function getMedicationAdherence(patientId: string, medicationId: string) {
  return apiFetch(`/medication-logs/${patientId}/medication/${medicationId}/adherence`) as Promise<AdherenceOut>;
}

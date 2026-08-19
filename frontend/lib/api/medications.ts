/**
 * lib/api/medications.ts
 * -------------------------
 * OWNED BY MEMBER 2 (Afifa) - Medication Management (README S6.2/S8.4).
 */

import { apiFetch } from "@/lib/apiClient";
// MedicationOut is defined in lib/api/dashboard.ts (same shape, used by
// both the dashboard summary card and this file's full CRUD) - imported
// here rather than redeclared to avoid an ambiguous re-export from
// lib/api.ts, which re-exports every api/*.ts file.
import type { MedicationOut } from "@/lib/api/dashboard";

export interface MedicationInput {
  medicine_name: string;
  dosage: string;
  frequency: string;
  start_date?: string | null;
  end_date?: string | null;
}

export function getMedications(patientId: string) {
  return apiFetch(`/medications/${patientId}`) as Promise<MedicationOut[]>;
}

export function createMedication(patientId: string, payload: MedicationInput) {
  return apiFetch(`/medications/${patientId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<MedicationOut>;
}

export function updateMedication(patientId: string, medicationId: string, payload: Partial<MedicationInput>) {
  return apiFetch(`/medications/${patientId}/${medicationId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  }) as Promise<MedicationOut>;
}

export function deleteMedication(patientId: string, medicationId: string) {
  return apiFetch(`/medications/${patientId}/${medicationId}`, { method: "DELETE" });
}

/**
 * lib/api/dashboard.ts
 * -----------------------
 * OWNED BY MEMBER 4 (Repai) - Module 1, Feature 4.
 */

import { apiFetch } from "@/lib/apiClient";

export interface VitalsOut {
  id: string;
  blood_pressure: string;
  sugar_level: number;
  heart_rate: number;
  temperature: number;
  logged_at: string;
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

export function getDashboard(patientId: string) {
  return apiFetch(`/dashboard/${patientId}`) as Promise<DashboardResponse>;
}

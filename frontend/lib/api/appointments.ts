/**
 * lib/api/appointments.ts
 * --------------------------
 * OWNED BY MEMBER 2 (Afifa) - Appointment Booking + Calendar Sync
 * (README S7.2). patient_name/patient_email are intentionally not part
 * of the input type - the backend always fills those in from the
 * patient's own account server-side, so there's nothing meaningful for
 * a form to collect for them.
 */

import { apiFetch } from "@/lib/apiClient";

// Full appointment detail, as returned by this file's endpoints. Named
// distinctly from lib/api/dashboard.ts's AppointmentOut (the smaller
// shape used by the dashboard summary widget) to avoid an ambiguous
// re-export from lib/api.ts, which re-exports every api/*.ts file.
export interface AppointmentDetail {
  id: string;
  patient_name: string;
  patient_email: string;
  doctor_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  reason: string | null;
  location: string | null;
  status: string;
  google_event_id: string | null;
}

export interface AppointmentInput {
  doctor_name: string;
  appointment_date: string;
  start_time: string;
  end_time: string;
  reason?: string;
  location?: string;
}

export function getAppointments(patientId: string) {
  return apiFetch(`/appointments/${patientId}`) as Promise<AppointmentDetail[]>;
}

export function bookAppointment(patientId: string, payload: AppointmentInput) {
  return apiFetch(`/appointments/${patientId}`, {
    method: "POST",
    // patient_name/patient_email are required by the backend schema but
    // ignored server-side in favor of the real patient record - sending
    // placeholders keeps the payload valid without asking the user for
    // information the server won't use anyway.
    body: JSON.stringify({ ...payload, patient_name: "", patient_email: "placeholder@careai.local" }),
  }) as Promise<AppointmentDetail>;
}

export function cancelAppointment(patientId: string, appointmentId: string) {
  return apiFetch(`/appointments/${patientId}/${appointmentId}`, { method: "DELETE" });
}

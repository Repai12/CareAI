/**
 * lib/api/visitNotes.ts
 * ------------------------
 * OWNED BY MEMBER 2 (Afifa) - Doctor Visit History & Prescriptions
 * (README S8.3). Only doctors can create notes; only the doctor who
 * wrote one can edit/archive it (the backend enforces this - see
 * doctor_id on VisitNoteOut, compared against the viewer's own id).
 */

import { apiFetch } from "@/lib/apiClient";

export interface VisitNoteOut {
  id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  appointment_id: string | null;
  visit_date: string;
  notes: string;
  prescription: string | null;
  status: string;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface VisitNoteInput {
  visit_date: string;
  notes: string;
  prescription?: string;
  appointment_id?: string;
}

export function getVisitNotes(patientId: string) {
  return apiFetch(`/visit-notes/${patientId}`) as Promise<VisitNoteOut[]>;
}

export function createVisitNote(patientId: string, payload: VisitNoteInput) {
  return apiFetch(`/visit-notes/${patientId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<VisitNoteOut>;
}

export function updateVisitNote(patientId: string, noteId: string, payload: { notes?: string; prescription?: string }) {
  return apiFetch(`/visit-notes/${patientId}/${noteId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  }) as Promise<VisitNoteOut>;
}

export function archiveVisitNote(patientId: string, noteId: string) {
  return apiFetch(`/visit-notes/${patientId}/${noteId}`, { method: "DELETE" });
}

export function summarizeVisitNote(patientId: string, noteId: string) {
  return apiFetch(`/visit-notes/${patientId}/${noteId}/summarize`, { method: "POST" }) as Promise<VisitNoteOut>;
}

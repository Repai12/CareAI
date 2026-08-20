/**
 * lib/api/patientQa.ts
 * -----------------------
 * Module 3: AI Patient History Q&A - doctor-only.
 */

import { apiFetch } from "@/lib/apiClient";

export interface PatientQuestionOut {
  id: string;
  patient_id: string;
  doctor_id: string;
  question: string;
  answer: string;
  created_at: string;
}

export function askPatientQuestion(patientId: string, question: string) {
  return apiFetch(`/patient-qa/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ question }),
  }) as Promise<PatientQuestionOut>;
}

export function getPatientQuestionHistory(patientId: string) {
  return apiFetch(`/patient-qa/${patientId}`) as Promise<PatientQuestionOut[]>;
}

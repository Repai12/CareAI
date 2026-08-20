/**
 * lib/api/companion.ts
 * -----------------------
 * Module 3: Dual-Persona AI Companion - patient-only.
 */

import { apiFetch } from "@/lib/apiClient";

export type CompanionPersona = "companion" | "coach";

export interface CompanionMessageOut {
  id: string;
  persona: CompanionPersona;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export function getCompanionHistory(patientId: string, persona: CompanionPersona) {
  return apiFetch(`/companion/${patientId}?persona=${persona}`) as Promise<CompanionMessageOut[]>;
}

export function sendCompanionMessage(patientId: string, persona: CompanionPersona, message: string) {
  return apiFetch(`/companion/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ persona, message }),
  }) as Promise<CompanionMessageOut>;
}

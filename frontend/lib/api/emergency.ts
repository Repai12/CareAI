/**
 * lib/api/emergency.ts
 * -----------------------
 * OWNED BY MEMBER 3 (Faisal) - Emergency Contacts, SOS, Falls, Daily
 * Check-ins (README S6.3/S7.3/S8.5/S8.6).
 */

import { apiFetch } from "@/lib/apiClient";

// --- Emergency contacts (README S6.3) ---

export interface EmergencyContactOut {
  id: string;
  user_id: string;
  name: string;
  phone: string;
  relationship: string;
  priority: number;
}

export interface EmergencyContactInput {
  name: string;
  phone: string;
  relationship: string;
  priority?: number;
}

export function getEmergencyContacts() {
  return apiFetch(`/api/emergency/contacts`) as Promise<EmergencyContactOut[]>;
}

export function addEmergencyContact(payload: EmergencyContactInput) {
  return apiFetch(`/api/emergency/contacts`, {
    method: "POST",
    body: JSON.stringify(payload),
  }) as Promise<EmergencyContactOut>;
}

export function updateEmergencyContact(contactId: string, payload: Partial<EmergencyContactInput>) {
  return apiFetch(`/api/emergency/contacts/${contactId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  }) as Promise<EmergencyContactOut>;
}

export function deleteEmergencyContact(contactId: string) {
  return apiFetch(`/api/emergency/contacts/${contactId}`, { method: "DELETE" });
}

export interface SosResult {
  status: string;
  message: string;
  delivered_to: string[];
  failed_to: string[];
  already_sent: boolean;
}

export function triggerSOS() {
  return apiFetch(`/api/emergency/sos`, { method: "POST" }) as Promise<SosResult>;
}

// --- Fall incident logger (README S8.5) ---

export interface FallIncidentOut {
  id: string;
  user_id: string;
  severity: string;
  details: string | null;
  occurred_at: string;
}

export function getFallHistory(patientId: string) {
  return apiFetch(`/fall-incidents/${patientId}`) as Promise<FallIncidentOut[]>;
}

export function logFallIncident(patientId: string, severity: string, details?: string) {
  return apiFetch(`/fall-incidents/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ severity, details }),
  }) as Promise<FallIncidentOut>;
}

// --- Daily safety check-in (README S8.6) ---

export interface SafetyCheckinOut {
  id: string;
  user_id: string;
  checked_in_at: string;
  is_checked_in: boolean;
}

export function checkIn() {
  return apiFetch(`/checkin`, { method: "POST" }) as Promise<SafetyCheckinOut>;
}

export function getCheckinHistory(patientId: string) {
  return apiFetch(`/checkin/${patientId}/history`) as Promise<SafetyCheckinOut[]>;
}

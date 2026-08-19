/**
 * lib/api/me.ts
 * ----------------
 * OWNED BY MEMBER 4 (Repai) - "who am I, which patients can I see,
 * who's waiting for my approval" endpoints. Backed by care_links
 * (README S4) - a link only grants dashboard access once status is
 * "active", which requires the patient to approve it first.
 */

import { apiFetch } from "@/lib/apiClient";

export interface CareLink {
  id: string;
  patient_id: string;
  patient_name: string;
  viewer_id: string;
  viewer_name: string;
  link_role: "family" | "doctor";
  relationship_label: string | null;
  permission_level: "view_only" | "view_and_manage";
  status: "pending" | "active" | "declined" | "revoked";
  created_at: string;
  responded_at: string | null;
  revoked_at: string | null;
}

export interface MyPatient {
  id: string;
  name: string;
  email: string;
  role: string;
  // Only ever set on a patient's own record - null on the User rows
  // returned for family/doctor viewers themselves (they don't have one).
  patient_code: string | null;
}

export function getMyPatients() {
  return apiFetch(`/me/patients`) as Promise<MyPatient[]>;
}

export function getMyConnections() {
  return apiFetch(`/me/connections`) as Promise<CareLink[]>;
}

export function approveConnection(linkId: string) {
  return apiFetch(`/me/connections/${linkId}/approve`, { method: "POST" }) as Promise<CareLink>;
}

export function declineConnection(linkId: string) {
  return apiFetch(`/me/connections/${linkId}/decline`, { method: "POST" }) as Promise<CareLink>;
}

export function revokeConnection(linkId: string) {
  return apiFetch(`/me/connections/${linkId}/revoke`, { method: "POST" }) as Promise<CareLink>;
}

export function updateConnectionPermission(linkId: string, permissionLevel: "view_only" | "view_and_manage") {
  return apiFetch(`/me/connections/${linkId}/permission`, {
    method: "POST",
    body: JSON.stringify({ permission_level: permissionLevel }),
  }) as Promise<CareLink>;
}

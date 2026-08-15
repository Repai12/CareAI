/**
 * lib/api/me.ts
 * ----------------
 * OWNED BY MEMBER 4 (Repai) - "who am I, which patients can I see,
 * who's waiting for my approval" endpoints.
 */

import { apiFetch } from "@/lib/apiClient";

export interface PendingRequest {
  link_id: string;
  viewer_name: string;
  viewer_email: string;
  relationship_label: string;
  requested_at: string;
}

export function getMyPatients() {
  return apiFetch(`/me/patients`) as Promise<{ id: string; name: string; email: string; role: string }[]>;
}

export function getPendingRequests() {
  return apiFetch(`/me/pending-requests`) as Promise<PendingRequest[]>;
}

export function decidePendingRequest(linkId: string, action: "approve" | "reject") {
  return apiFetch(`/me/pending-requests/${linkId}/${action}`, { method: "POST" });
}

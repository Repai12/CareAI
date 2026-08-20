/**
 * lib/api/chat.ts
 * ------------------
 * Module 3: Family Chat over WebSockets. History loads over REST before
 * the socket connects; the socket (opened directly by the chat page, not
 * from here - it needs the live connection object) carries new messages.
 */

import { apiFetch } from "@/lib/apiClient";

export interface ChatMessageOut {
  id: string;
  patient_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: string;
  content: string;
  created_at: string;
}

export function getChatHistory(patientId: string, limit = 50) {
  return apiFetch(`/chat/${patientId}/messages?limit=${limit}`) as Promise<ChatMessageOut[]>;
}

/** Same origin as NEXT_PUBLIC_API_URL, with http(s) swapped for ws(s). */
export function getChatWebSocketUrl(patientId: string, token: string): string {
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const wsBase = apiBase.replace(/^http/, "ws");
  return `${wsBase}/ws/chat/${patientId}?token=${encodeURIComponent(token)}`;
}

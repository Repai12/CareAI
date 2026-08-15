/**
 * lib/api/notifications.ts
 * ---------------------------
 * OWNED BY MEMBER 4 (Repai) - Module 3, Feature 8.
 */

import { apiFetch } from "@/lib/apiClient";

export interface NotificationOut {
  id: string;
  event_type: string;
  title: string;
  message: string;
  category: string;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPage {
  items: NotificationOut[];
  next_cursor: string | null;
}

export function getNotifications(patientId: string, category?: string, before?: string) {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (before) params.set("before", before);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return apiFetch(`/notifications/${patientId}${qs}`) as Promise<NotificationPage>;
}

export function markNotificationsRead(patientId: string, notificationIds?: string[]) {
  return apiFetch(`/notifications/${patientId}/mark-read`, {
    method: "POST",
    body: JSON.stringify({ notification_ids: notificationIds }),
  }) as Promise<{ marked_read: number }>;
}

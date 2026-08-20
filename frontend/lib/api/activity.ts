/**
 * lib/api/activity.ts
 * ----------------------
 * Module 1: Activity Tracking ("Activity tracking with trend
 * dashboards" - README Features table).
 */

import { apiFetch } from "@/lib/apiClient";

export type ActivityType = "walk" | "exercise" | "chores" | "other";

export interface ActivityLogOut {
  id: string;
  activity_type: ActivityType;
  duration_minutes: number;
  note: string | null;
  logged_at: string;
}

export function logActivity(patientId: string, activityType: ActivityType, durationMinutes: number, note?: string) {
  return apiFetch(`/activity/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ activity_type: activityType, duration_minutes: durationMinutes, note: note || undefined }),
  }) as Promise<ActivityLogOut>;
}

export function getActivityHistory(patientId: string, limit = 30) {
  return apiFetch(`/activity/${patientId}?limit=${limit}`) as Promise<ActivityLogOut[]>;
}

export function deleteActivity(patientId: string, activityId: string) {
  return apiFetch(`/activity/${patientId}/${activityId}`, { method: "DELETE" });
}

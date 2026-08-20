/**
 * lib/api/mood.ts
 * ------------------
 * Module 1: Mood Tracking.
 */

import { apiFetch } from "@/lib/apiClient";

export type MoodLevel = "great" | "good" | "okay" | "low" | "bad";

export interface MoodLogOut {
  id: string;
  mood: MoodLevel;
  note: string | null;
  logged_at: string;
}

export function logMood(patientId: string, mood: MoodLevel, note?: string) {
  return apiFetch(`/mood/${patientId}`, {
    method: "POST",
    body: JSON.stringify({ mood, note: note || undefined }),
  }) as Promise<MoodLogOut>;
}

export function getMoodHistory(patientId: string, limit = 14) {
  return apiFetch(`/mood/${patientId}?limit=${limit}`) as Promise<MoodLogOut[]>;
}

export function deleteMood(patientId: string, moodId: string) {
  return apiFetch(`/mood/${patientId}/${moodId}`, { method: "DELETE" });
}

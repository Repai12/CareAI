/**
 * lib/api/wellness.ts
 * ----------------------
 * Module 2: Wellness Recommendation Engine ("wellness recommendation
 * engine" - README Features table, distinct from the nutrition
 * planner/Diet Advisor).
 */

import { apiFetch } from "@/lib/apiClient";

export interface WellnessRecommendationOut {
  id: string;
  based_on_summary: string;
  recommendations: string;
  created_at: string;
}

export function generateWellnessRecommendations(patientId: string) {
  return apiFetch(`/wellness/${patientId}/generate`, { method: "POST" }) as Promise<WellnessRecommendationOut>;
}

export function getLatestWellness(patientId: string) {
  return apiFetch(`/wellness/${patientId}/latest`) as Promise<WellnessRecommendationOut | null>;
}

/**
 * lib/api/reports.ts
 * ---------------------
 * OWNED BY MEMBER 4 (Repai) - Module 2/4 (Weekly Report) and
 * Module 3/7 (Doctor AI Summary).
 */

import { apiFetch } from "@/lib/apiClient";

export interface WeeklyReportOut {
  id: string;
  patient_id: string;
  recipient_email: string;
  report_type: string;
  status: string;
  sent_at: string;
}

export function triggerWeeklyReport(patientId: string) {
  return apiFetch(`/reports/weekly/trigger`, {
    method: "POST",
    body: JSON.stringify({ patient_id: patientId }),
  }) as Promise<WeeklyReportOut[]>;
}

export function getReportHistory(patientId: string) {
  return apiFetch(`/reports/weekly/${patientId}`) as Promise<WeeklyReportOut[]>;
}

export function triggerAISummary(patientId: string) {
  return apiFetch(`/reports/ai-summary/${patientId}`, {
    method: "POST",
  }) as Promise<WeeklyReportOut>;
}

/**
 * lib/api.ts
 * -------------
 * SHARED FILE - but the ONLY thing that should ever change here is
 * adding one export line for your own new file under lib/api/. Never
 * add actual logic here - put it in your own file (lib/api/vitals.ts,
 * lib/api/medications.ts, etc.) and just re-export it below.
 *
 * This exists so existing imports like `from "@/lib/api"` keep working
 * without every component needing to change its import path.
 */

export * from "./apiClient";
export * from "./api/auth";
export * from "./api/dashboard";
export * from "./api/reports";
export * from "./api/me";
export * from "./api/notifications";
export * from "./api/vitals";
export * from "./api/medications";
export * from "./api/appointments";
export * from "./api/medicationLogs";
export * from "./api/visitNotes";
export * from "./api/emergency";
export * from "./api/mood";
export * from "./api/patientQa";
export * from "./api/chat";
export * from "./api/activity";
export * from "./api/wellness";

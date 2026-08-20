"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getActivityHistory, ActivityLogOut } from "@/lib/api/activity";
import HealthNav from "../../_components/HealthNav";
import ActivityTrackerPanel from "../../_components/ActivityTrackerPanel";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function ActivityPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [logs, setLogs] = useState<ActivityLogOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;
    getActivityHistory(patientId, 60)
      .then(setLogs)
      .catch((e) => setError(e.message));
  }, [patientId]);

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">Activity Tracking</h1>
      </header>

      <HealthNav patientId={patientId} current="activity" />

      {error && <p className="text-alert">{error}</p>}
      {!error && !logs && <p className="text-ink/50">Loading...</p>}
      {logs && <ActivityTrackerPanel patientId={patientId} isOwner={role === "patient"} initialLogs={logs} />}
    </main>
  );
}

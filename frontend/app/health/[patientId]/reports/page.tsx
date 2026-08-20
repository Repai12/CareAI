"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getHealthReports, HealthReportOut } from "@/lib/api/vitals";
import HealthNav from "../../_components/HealthNav";
import ReportAnalyzerPanel from "../../_components/ReportAnalyzerPanel";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function ReportsPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [reports, setReports] = useState<HealthReportOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;
    getHealthReports(patientId)
      .then(setReports)
      .catch((e) => setError(e.message));
  }, [patientId]);

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module (Member 1)</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">AI Health Report Analyzer</h1>
      </header>

      <HealthNav patientId={patientId} current="reports" />

      {error && <p className="text-alert">{error}</p>}
      {!error && !reports && <p className="text-ink/50">Loading...</p>}
      {reports && <ReportAnalyzerPanel isOwner={role === "patient"} initialReports={reports} />}
    </main>
  );
}

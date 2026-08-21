"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getVitalsHistory, VitalsEntryOut } from "@/lib/api/vitals";
import HealthNav from "../../_components/HealthNav";
import VitalsPanel from "../../_components/VitalsPanel";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function VitalsPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [history, setHistory] = useState<VitalsEntryOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;
    getVitalsHistory(patientId)
      .then(setHistory)
      .catch((e) => setError(e.message));
  }, [patientId]);

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">Vitals Logging</h1>
      </header>

      <HealthNav patientId={patientId} current="vitals" />

      {error && <p className="text-alert">{error}</p>}
      {!error && !history && <p className="text-ink/50">Loading...</p>}
      {history && <VitalsPanel patientId={patientId} isOwner={role === "patient"} initialHistory={history} />}
    </main>
  );
}

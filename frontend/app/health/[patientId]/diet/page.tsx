"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getLatestDietPlan, DietPlanWithLogs } from "@/lib/api/vitals";
import HealthNav from "../../_components/HealthNav";
import DietAdvisorPanel from "../../_components/DietAdvisorPanel";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function DietPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [data, setData] = useState<DietPlanWithLogs | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;
    getLatestDietPlan(patientId)
      .then(setData)
      .catch((e) => setError(e.message));
  }, [patientId]);

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module (Member 1)</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">AI Diet Advisor</h1>
      </header>

      <HealthNav patientId={patientId} current="diet" />

      {error && <p className="text-alert">{error}</p>}
      {!error && !data && <p className="text-ink/50">Loading...</p>}
      {data && <DietAdvisorPanel isOwner={role === "patient"} initial={data} />}
    </main>
  );
}

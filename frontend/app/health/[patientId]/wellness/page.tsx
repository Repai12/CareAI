"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getLatestWellness, WellnessRecommendationOut } from "@/lib/api/wellness";
import HealthNav from "../../_components/HealthNav";
import WellnessPanel from "../../_components/WellnessPanel";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function WellnessPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [latest, setLatest] = useState<WellnessRecommendationOut | null | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;
    getLatestWellness(patientId)
      .then(setLatest)
      .catch((e) => setError(e.message));
  }, [patientId]);

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">Wellness Recommendations</h1>
      </header>

      <HealthNav patientId={patientId} current="wellness" />

      {error && <p className="text-alert">{error}</p>}
      {!error && latest === undefined && <p className="text-ink/50">Loading...</p>}
      {latest !== undefined && <WellnessPanel patientId={patientId} isOwner={role === "patient"} initial={latest} />}
    </main>
  );
}

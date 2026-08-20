"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { SparkleIcon } from "./icons";
import { WellnessRecommendationOut, generateWellnessRecommendations } from "@/lib/api/wellness";

export default function WellnessPanel({
  patientId,
  isOwner,
  initial,
}: {
  patientId: string;
  isOwner: boolean;
  initial: WellnessRecommendationOut | null;
}) {
  const [latest, setLatest] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const result = await generateWellnessRecommendations(patientId);
      setLatest(result);
    } catch (e: any) {
      setError(e.message || "Wellness recommendations are temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard
      eyebrow="Module 2 · Wellness Recommendation Engine"
      title="Wellness tips"
      icon={<SparkleIcon />}
      accent="gold"
      disclaimer="AI-generated lifestyle tips, not medical advice - check with your doctor for anything medical."
    >
      {isOwner && (
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="bg-gold text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition mb-4"
        >
          {loading ? "Thinking..." : latest ? "Refresh recommendations" : "Get wellness tips"}
        </button>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {latest ? (
        <div className="bg-paper rounded-lg p-4 whitespace-pre-line text-sm text-ink">{latest.recommendations}</div>
      ) : (
        <p className="text-ink/50 text-sm">No wellness recommendations yet.</p>
      )}
      {latest && (
        <p className="text-xs text-ink/40 mt-2">Generated {new Date(latest.created_at).toLocaleString()}</p>
      )}
    </SectionCard>
  );
}

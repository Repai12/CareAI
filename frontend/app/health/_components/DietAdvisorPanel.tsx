"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { LeafIcon } from "./icons";
import { DietPlanWithLogs, generateDietPlan, logDietAdherence } from "@/lib/api/vitals";

export default function DietAdvisorPanel({
  isOwner,
  initial,
}: {
  isOwner: boolean;
  initial: DietPlanWithLogs;
}) {
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [logging, setLogging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    setLoading(true);
    try {
      const plan = await generateDietPlan();
      setData({ plan, logs: [], adherence_rate: null });
    } catch (e: any) {
      setError(e.message || "Failed to generate diet plan");
    } finally {
      setLoading(false);
    }
  }

  async function handleLog(followed: boolean) {
    if (!data.plan) return;
    setLogging(true);
    setError(null);
    try {
      const log = await logDietAdherence(data.plan.id, followed);
      const newLogs = [log, ...data.logs];
      const followedCount = newLogs.filter((l) => l.followed).length;
      setData({ ...data, logs: newLogs, adherence_rate: Math.round((followedCount / newLogs.length) * 100) });
    } catch (e: any) {
      setError(e.message || "Failed to log adherence");
    } finally {
      setLogging(false);
    }
  }

  return (
    <SectionCard eyebrow="Feature 4 · Groq, trend-aware + adherence tracking" title="AI Diet Advisor" icon={<LeafIcon />} accent="sage">
      {isOwner && (
        <button
          onClick={handleGenerate} disabled={loading}
          className="bg-sage text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition mb-4"
        >
          {loading ? "Generating..." : data.plan ? "Regenerate plan from latest vitals" : "Generate my diet plan"}
        </button>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {!data.plan ? (
        <p className="text-ink/50 text-sm">No diet plan yet.</p>
      ) : (
        <div>
          <p className="text-xs text-ink/40 italic mb-2">Based on: {data.plan.based_on_summary}</p>
          <p className="text-sm text-ink whitespace-pre-wrap bg-sageLight/50 rounded-lg p-3">{data.plan.ai_plan}</p>

          {isOwner && (
            <div className="flex items-center gap-2 mt-3">
              <span className="text-xs text-ink/50">Followed today?</span>
              <button
                onClick={() => handleLog(true)} disabled={logging}
                className="text-xs font-medium bg-sage/10 text-sage px-3 py-1 rounded-full hover:bg-sage/20 disabled:opacity-50 transition"
              >
                Yes
              </button>
              <button
                onClick={() => handleLog(false)} disabled={logging}
                className="text-xs font-medium bg-alert/10 text-alert px-3 py-1 rounded-full hover:bg-alert/20 disabled:opacity-50 transition"
              >
                No
              </button>
              {data.adherence_rate !== null && (
                <span className="text-xs text-ink/50 ml-auto">{data.adherence_rate}% adherence ({data.logs.length} logs)</span>
              )}
            </div>
          )}
        </div>
      )}
    </SectionCard>
  );
}

"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { StethoscopeIcon } from "./icons";
import { SymptomLogOut, checkSymptoms } from "@/lib/api/vitals";

const URGENCY_STYLES: Record<SymptomLogOut["urgency"], string> = {
  normal: "bg-sageLight text-sage",
  monitor: "bg-gold/15 text-gold",
  urgent: "bg-alert/10 text-alert",
  emergency: "bg-alert text-white",
};

export default function SymptomCheckerPanel({
  isOwner,
  initialLogs,
}: {
  isOwner: boolean;
  initialLogs: SymptomLogOut[];
}) {
  const [symptoms, setSymptoms] = useState("");
  const [logs, setLogs] = useState(initialLogs);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!symptoms.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const log = await checkSymptoms(symptoms);
      setLogs([log, ...logs]);
      setSymptoms("");
    } catch (e: any) {
      setError(e.message || "Failed to check symptoms");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard eyebrow="Feature 3 · Groq, vitals-aware + auto-escalation" title="AI Symptom Checker" icon={<StethoscopeIcon />} accent="alert">
      {isOwner && (
        <form onSubmit={handleSubmit} className="mb-4">
          <textarea
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="Describe how you're feeling, e.g. 'dizzy and short of breath since this morning'"
            rows={2}
            className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-sage"
          />
          <button
            type="submit" disabled={loading}
            className="bg-alert text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
          >
            {loading ? "Checking..." : "Check symptoms"}
          </button>
        </form>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {logs.length === 0 ? (
        <p className="text-ink/50 text-sm">No symptom checks yet.</p>
      ) : (
        <ul className="space-y-3 max-h-72 overflow-y-auto">
          {logs.map((l) => (
            <li key={l.id} className="border border-sageLight rounded-lg px-3 py-2">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-ink/70 italic">&ldquo;{l.symptoms}&rdquo;</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full shrink-0 ml-2 ${URGENCY_STYLES[l.urgency]}`}>
                  {l.urgency}
                </span>
              </div>
              <p className="text-sm text-ink">{l.ai_response}</p>
              {l.escalated && (
                <p className="text-xs text-alert font-medium mt-1">Family was automatically notified of this emergency.</p>
              )}
              <p className="text-ink/40 text-xs mt-1">{new Date(l.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

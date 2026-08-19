"use client";

import { useState } from "react";
import SectionCard from "./SectionCard";
import { MailIcon } from "./icons";
import { apiFetch } from "@/lib/api";

/**
 * Doctor-only panel - Module 3, Feature 7: Doctor AI Patient Summary Email.
 * Only renders anything if the logged-in user's role is "doctor" (checked
 * by the parent dashboard page before mounting this component).
 */
export default function AISummaryPanel({ patientId }: { patientId: string }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; sent_at: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const log = await apiFetch(`/reports/ai-summary/${patientId}`, { method: "POST" });
      setResult(log);
    } catch (e: any) {
      setError(e.message || "Failed to generate summary");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard
      eyebrow="Gemini + Resend"
      title="AI Patient Summary"
      icon={<MailIcon />}
      accent="steel"
      disclaimer="AI-generated clinical summary, not a diagnosis - review before acting on it."
    >
      <p className="text-sm text-ink/60 mb-3">
        Generates a plain-English clinical summary of the last 30 days and emails it to you.
      </p>
      <button
        onClick={handleGenerate}
        disabled={loading}
        className="bg-steel text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
      >
        {loading ? "Generating..." : "Generate AI Summary"}
      </button>

      {error && <p className="text-alert text-sm mt-3">{error}</p>}
      {result && (
        <p className="text-sm text-sage mt-3">
          {result.status === "SENT" ? "Summary sent to your email." : "Failed to send - try again."}
        </p>
      )}
    </SectionCard>
  );
}

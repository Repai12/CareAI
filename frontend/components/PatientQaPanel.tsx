"use client";

import { useEffect, useState } from "react";
import SectionCard from "./SectionCard";
import { HeartPulseIcon } from "./icons";
import { PatientQuestionOut, askPatientQuestion, getPatientQuestionHistory } from "@/lib/api/patientQa";

/**
 * Doctor-only panel - README Features table: "Doctor ... uses AI to
 * analyze reports, answers patient-history questions". Only renders
 * anything useful when mounted by a doctor viewing an actively-linked
 * patient (the backend re-checks this regardless).
 */
export default function PatientQaPanel({ patientId }: { patientId: string }) {
  const [history, setHistory] = useState<PatientQuestionOut[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPatientQuestionHistory(patientId)
      .then(setHistory)
      .catch(() => {});
  }, [patientId]);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const entry = await askPatientQuestion(patientId, question);
      setHistory((prev) => [entry, ...prev]);
      setQuestion("");
    } catch (e: any) {
      setError(e.message || "AI answer is temporarily unavailable.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard
      eyebrow="AI Patient History Q&A"
      title="Ask about this patient's history"
      icon={<HeartPulseIcon />}
      accent="steel"
      disclaimer="AI-generated answer grounded in this patient's records, not a diagnosis - verify before acting on it."
    >
      <form onSubmit={handleAsk} className="mb-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. 'Has their blood pressure trended up recently?' or 'What was discussed at the last visit?'"
          rows={2}
          className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-sage"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-steel text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {history.length === 0 ? (
        <p className="text-ink/50 text-sm">No questions asked yet.</p>
      ) : (
        <ul className="space-y-3 max-h-96 overflow-y-auto">
          {history.map((h) => (
            <li key={h.id} className="border border-sageLight rounded-lg px-3 py-2">
              <p className="text-sm text-ink/70 italic mb-1">&ldquo;{h.question}&rdquo;</p>
              <p className="text-sm text-ink">{h.answer}</p>
              <p className="text-ink/40 text-xs mt-1">{new Date(h.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

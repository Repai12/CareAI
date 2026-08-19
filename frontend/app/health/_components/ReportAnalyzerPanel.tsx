"use client";

import { useRef, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { DocumentSearchIcon } from "./icons";
import { HealthReportOut, uploadHealthReport } from "@/lib/api/vitals";

export default function ReportAnalyzerPanel({
  isOwner,
  initialReports,
}: {
  isOwner: boolean;
  initialReports: HealthReportOut[];
}) {
  const [reports, setReports] = useState(initialReports);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function handleUpload() {
    const file = fileInput.current?.files?.[0];
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const report = await uploadHealthReport(file);
      setReports([report, ...reports]);
      if (fileInput.current) fileInput.current.value = "";
    } catch (e: any) {
      setError(e.message || "Failed to analyze report");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard
      eyebrow="Feature 2 · Groq API LIVE"
      title="AI Health Report Analyzer"
      icon={<DocumentSearchIcon />}
      accent="gold"
      disclaimer="AI-generated summary, not a diagnosis. Always confirm findings with a doctor."
    >
      {isOwner && (
        <div className="flex items-center gap-2 mb-4">
          <input ref={fileInput} type="file" accept="application/pdf" className="text-sm text-ink/70 flex-1" />
          <button
            onClick={handleUpload} disabled={loading}
            className="bg-gold text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition shrink-0"
          >
            {loading ? "Analyzing..." : "Upload & analyze"}
          </button>
        </div>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {reports.length === 0 ? (
        <p className="text-ink/50 text-sm">No reports uploaded yet.</p>
      ) : (
        <ul className="space-y-3 max-h-72 overflow-y-auto">
          {reports.map((r) => (
            <li key={r.id} className="border border-sageLight rounded-lg px-3 py-2">
              <div className="flex justify-between items-baseline">
                <span className="font-medium text-ink text-sm">{r.filename}</span>
                <span className="text-ink/40 text-xs">{new Date(r.created_at).toLocaleDateString()}</span>
              </div>
              {r.flagged_values.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2 mb-1">
                  {r.flagged_values.map((f, i) => (
                    <span
                      key={i}
                      className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        f.status === "high" ? "bg-alert text-white" : f.status === "low" ? "bg-gold text-white" : "bg-sageLight text-sage"
                      }`}
                    >
                      {f.label}: {f.value} — {f.status.toUpperCase()}
                    </span>
                  ))}
                </div>
              )}
              <p className="text-ink/70 text-sm mt-1 whitespace-pre-wrap">{r.ai_summary}</p>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

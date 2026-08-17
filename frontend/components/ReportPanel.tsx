"use client";

import { useState } from "react";
import SectionCard from "./SectionCard";
import { MailIcon } from "./icons";
import { WeeklyReportOut, triggerWeeklyReport } from "@/lib/api";

export default function ReportPanel({
  patientId,
  initialHistory,
}: {
  patientId: string;
  initialHistory: WeeklyReportOut[];
}) {
  const [history, setHistory] = useState(initialHistory);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSendNow() {
    setLoading(true);
    setError(null);
    try {
      const logs = await triggerWeeklyReport(patientId);
      setHistory([...logs, ...history]);
    } catch (e: any) {
      setError(e.message || "Failed to send report");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SectionCard eyebrow="Resend" title="Weekly Email Health Report" icon={<MailIcon />} accent="sage">
      <button
        onClick={handleSendNow}
        disabled={loading}
        className="bg-sage text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
      >
        {loading ? "Sending..." : "Send report now"}
      </button>

      {error && <p className="text-alert text-sm mt-2">{error}</p>}

      <div className="mt-5">
        <p className="text-xs uppercase tracking-wide text-ink/40 font-semibold mb-2">
          Send history
        </p>
        {history.length === 0 ? (
          <p className="text-ink/50 text-sm">No reports sent yet this week.</p>
        ) : (
          <ul className="space-y-2">
            {history.map((r) => (
              <li key={r.id} className="text-sm flex justify-between border-b border-sageLight pb-2">
                <span className="text-ink/70">{r.sent_to}</span>
                <span className={r.status === "sent" ? "text-sage" : "text-alert"}>
                  {r.status} · {new Date(r.sent_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </SectionCard>
  );
}

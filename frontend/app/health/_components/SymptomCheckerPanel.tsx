"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { StethoscopeIcon } from "./icons";
import { SymptomLogOut, checkSymptoms, replySymptomCheck } from "@/lib/api/vitals";

const URGENCY_STYLES: Record<SymptomLogOut["urgency"], string> = {
  normal: "bg-sageLight text-sage",
  monitor: "bg-gold/15 text-gold",
  urgent: "bg-alert/10 text-alert",
  emergency: "bg-alert text-white",
};

function Entry({ log }: { log: SymptomLogOut }) {
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm text-ink/70 italic">&ldquo;{log.symptoms}&rdquo;</span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full shrink-0 ml-2 ${URGENCY_STYLES[log.urgency]}`}>
          {log.urgency}
        </span>
      </div>
      <p className="text-sm text-ink">{log.ai_response}</p>
      {log.escalated && (
        <p className="text-xs text-alert font-medium mt-1">Family was automatically notified of this emergency.</p>
      )}
      <p className="text-ink/40 text-xs mt-1">{new Date(log.created_at).toLocaleString()}</p>
    </div>
  );
}

function Thread({
  root,
  replies,
  isOwner,
  onReply,
}: {
  root: SymptomLogOut;
  replies: SymptomLogOut[];
  isOwner: boolean;
  onReply: (rootId: string, message: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleReply(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    setLoading(true);
    try {
      await onReply(root.id, draft);
      setDraft("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <li className="border border-sageLight rounded-lg px-3 py-2">
      <Entry log={root} />
      {replies.length > 0 && (
        <div className="mt-2 ml-4 pl-3 border-l-2 border-sageLight space-y-2">
          {replies.map((r) => (
            <Entry key={r.id} log={r} />
          ))}
        </div>
      )}
      {isOwner && (
        <form onSubmit={handleReply} className="mt-2 flex gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Add more detail, e.g. 'it's gotten worse'..."
            className="flex-1 border border-sageLight rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-sage"
          />
          <button
            type="submit"
            disabled={loading}
            className="text-xs font-medium bg-alert/10 text-alert px-3 py-1 rounded-lg hover:bg-alert/20 disabled:opacity-50 transition shrink-0"
          >
            {loading ? "..." : "Reply"}
          </button>
        </form>
      )}
    </li>
  );
}

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

  async function handleReply(rootId: string, message: string) {
    setError(null);
    try {
      const reply = await replySymptomCheck(rootId, message);
      setLogs([reply, ...logs]);
    } catch (e: any) {
      setError(e.message || "Failed to send reply");
    }
  }

  const roots = logs.filter((l) => !l.parent_id);
  const repliesByRoot = new Map<string, SymptomLogOut[]>();
  for (const l of logs) {
    if (l.parent_id) {
      const list = repliesByRoot.get(l.parent_id) || [];
      list.push(l);
      repliesByRoot.set(l.parent_id, list);
    }
  }
  for (const list of repliesByRoot.values()) {
    list.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
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

      {roots.length === 0 ? (
        <p className="text-ink/50 text-sm">No symptom checks yet.</p>
      ) : (
        <ul className="space-y-3 max-h-96 overflow-y-auto">
          {roots.map((root) => (
            <Thread key={root.id} root={root} replies={repliesByRoot.get(root.id) || []} isOwner={isOwner} onReply={handleReply} />
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

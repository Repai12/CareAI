"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getCompanionHistory,
  sendCompanionMessage,
  type CompanionMessageOut,
  type CompanionPersona,
} from "@/lib/api";
import { getMyRole } from "@/lib/apiClient";

const PERSONAS: { value: CompanionPersona; label: string; blurb: string; accent: string }[] = [
  { value: "companion", label: "Companion", blurb: "warm company, casual chat", accent: "sage" },
  { value: "coach", label: "Coach", blurb: "friendly nudges toward healthy habits", accent: "steel" },
];

export default function CompanionPage() {
  const params = useParams<{ patientId: string }>();
  const router = useRouter();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [persona, setPersona] = useState<CompanionPersona>("companion");
  const [messages, setMessages] = useState<CompanionMessageOut[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setRole(getMyRole());
  }, []);

  useEffect(() => {
    if (!patientId) return;
    setHistoryLoading(true);
    setError(null);
    getCompanionHistory(patientId, persona)
      .then(setMessages)
      .catch((e) => setError(e.message))
      .finally(() => setHistoryLoading(false));
  }, [patientId, persona]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!draft.trim() || loading) return;
    setLoading(true);
    setError(null);
    const text = draft.trim();
    try {
      // Optimistic: show the user's own message immediately, then append
      // the assistant's reply once it arrives (the backend only persists
      // the user turn once a reply actually succeeds - see companion.py).
      setMessages((prev) => [
        ...prev,
        { id: `pending-${Date.now()}`, persona, role: "user", content: text, created_at: new Date().toISOString() },
      ]);
      setDraft("");
      const reply = await sendCompanionMessage(patientId, persona, text);
      setMessages((prev) => [...prev, reply]);
    } catch (e: any) {
      setError(e.message || "The AI companion is temporarily unavailable.");
      // Drop the optimistic bubble since the backend never persisted it either.
      setMessages((prev) => prev.filter((m) => !m.id.startsWith("pending-")));
      setDraft(text);
    } finally {
      setLoading(false);
    }
  }

  if (role !== null && role !== "patient") {
    return (
      <main className="min-h-screen flex items-center justify-center px-6">
        <p className="text-ink/50 text-sm">The AI companion is only available to the patient themselves.</p>
      </main>
    );
  }

  const active = PERSONAS.find((p) => p.value === persona)!;

  return (
    <main className="min-h-screen px-6 py-10 max-w-2xl mx-auto flex flex-col">
      <header className="mb-4">
        <p className="text-sm text-sage font-medium">CareAI · AI Companion</p>
        <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Chat with your AI companion</h1>
        <p className="text-xs text-ink/40 italic mt-1">
          AI-generated conversation, not a substitute for real human contact or medical advice.
        </p>
      </header>

      <div className="flex gap-2 mb-4">
        {PERSONAS.map((p) => (
          <button
            key={p.value}
            onClick={() => setPersona(p.value)}
            className={`flex-1 text-left rounded-xl border px-4 py-2.5 transition ${
              persona === p.value ? "border-sage bg-sageLight" : "border-sageLight hover:bg-sageLight/50"
            }`}
          >
            <p className="text-sm font-semibold text-ink">{p.label}</p>
            <p className="text-xs text-ink/50">{p.blurb}</p>
          </button>
        ))}
      </div>

      <div className="flex-1 bg-white border border-sageLight rounded-xl p-4 min-h-[360px] max-h-[480px] overflow-y-auto flex flex-col gap-3">
        {historyLoading && <p className="text-ink/40 text-sm">Loading...</p>}
        {!historyLoading && messages.length === 0 && (
          <p className="text-ink/40 text-sm">
            Say hello to your {active.label.toLowerCase()} to start the conversation.
          </p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[75%] rounded-2xl px-3.5 py-2 text-sm ${
                m.role === "user" ? "bg-sage text-white" : "bg-sageLight text-ink"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-alert text-sm mt-2">{error}</p>}

      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Message your ${active.label.toLowerCase()}...`}
          maxLength={2000}
          disabled={loading}
          className="flex-1 border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !draft.trim()}
          className="bg-sage text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
        >
          {loading ? "..." : "Send"}
        </button>
      </form>

      <button onClick={() => router.back()} className="inline-block mt-6 text-sm text-sage font-medium hover:underline self-start">
        Back
      </button>
    </main>
  );
}

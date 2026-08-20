"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { SmileIcon } from "./icons";
import { MoodLogOut, MoodLevel, logMood } from "@/lib/api/mood";

const MOODS: { value: MoodLevel; emoji: string; label: string }[] = [
  { value: "great", emoji: "😄", label: "Great" },
  { value: "good", emoji: "🙂", label: "Good" },
  { value: "okay", emoji: "😐", label: "Okay" },
  { value: "low", emoji: "🙁", label: "Low" },
  { value: "bad", emoji: "😞", label: "Bad" },
];

const MOOD_DOT: Record<MoodLevel, string> = {
  great: "bg-sage",
  good: "bg-sage/60",
  okay: "bg-gold/60",
  low: "bg-alert/50",
  bad: "bg-alert",
};

export default function MoodTrackerPanel({
  patientId,
  isOwner,
  initialLogs,
}: {
  patientId: string;
  isOwner: boolean;
  initialLogs: MoodLogOut[];
}) {
  const [logs, setLogs] = useState(initialLogs);
  const [note, setNote] = useState("");
  const [selected, setSelected] = useState<MoodLevel | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLog(mood: MoodLevel) {
    setSelected(mood);
    setError(null);
    setLoading(true);
    try {
      const entry = await logMood(patientId, mood, note.trim() || undefined);
      setLogs([entry, ...logs]);
      setNote("");
    } catch (e: any) {
      setError(e.message || "Failed to log mood");
    } finally {
      setLoading(false);
      setSelected(null);
    }
  }

  return (
    <SectionCard eyebrow="Module 1 · Mood Tracking" title="How are you feeling?" icon={<SmileIcon />} accent="gold">
      {isOwner && (
        <div className="mb-5">
          <div className="grid grid-cols-5 gap-2 mb-3">
            {MOODS.map((m) => (
              <button
                key={m.value}
                type="button"
                disabled={loading}
                onClick={() => handleLog(m.value)}
                className={`flex flex-col items-center gap-1 py-3 rounded-xl border transition disabled:opacity-50 ${
                  selected === m.value ? "border-gold bg-gold/10" : "border-sageLight hover:bg-sageLight"
                }`}
              >
                <span className="text-2xl">{m.emoji}</span>
                <span className="text-xs font-medium text-ink/70">{m.label}</span>
              </button>
            ))}
          </div>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note, e.g. 'slept badly'"
            className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
          />
        </div>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      {logs.length === 0 ? (
        <p className="text-ink/50 text-sm">No mood logged yet.</p>
      ) : (
        <>
          <div className="flex gap-1.5 mb-4">
            {[...logs]
              .slice(0, 14)
              .reverse()
              .map((l) => (
                <span
                  key={l.id}
                  title={`${l.mood} · ${new Date(l.logged_at).toLocaleString()}`}
                  className={`w-3 h-3 rounded-full ${MOOD_DOT[l.mood]}`}
                />
              ))}
          </div>
          <ul className="space-y-2 max-h-72 overflow-y-auto">
            {logs.map((l) => (
              <li key={l.id} className="flex items-start justify-between border border-sageLight rounded-lg px-3 py-2">
                <div>
                  <span className="text-sm font-medium text-ink capitalize">
                    {MOODS.find((m) => m.value === l.mood)?.emoji} {l.mood}
                  </span>
                  {l.note && <p className="text-xs text-ink/60 mt-0.5">{l.note}</p>}
                </div>
                <span className="text-xs text-ink/40 shrink-0 ml-2">{new Date(l.logged_at).toLocaleString()}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </SectionCard>
  );
}

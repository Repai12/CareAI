"use client";

import { useMemo, useState } from "react";
import SectionCard from "@/components/SectionCard";
import { ActivityIcon } from "./icons";
import { ActivityLogOut, ActivityType, logActivity, deleteActivity } from "@/lib/api/activity";

const TYPES: { value: ActivityType; emoji: string; label: string }[] = [
  { value: "walk", emoji: "🚶", label: "Walk" },
  { value: "exercise", emoji: "🏋️", label: "Exercise" },
  { value: "chores", emoji: "🧹", label: "Chores" },
  { value: "other", emoji: "⭐", label: "Other" },
];

function dayKey(iso: string) {
  return new Date(iso).toISOString().slice(0, 10);
}

export default function ActivityTrackerPanel({
  patientId,
  isOwner,
  initialLogs,
}: {
  patientId: string;
  isOwner: boolean;
  initialLogs: ActivityLogOut[];
}) {
  const [logs, setLogs] = useState(initialLogs);
  const [type, setType] = useState<ActivityType>("walk");
  const [minutes, setMinutes] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLog(e: React.FormEvent) {
    e.preventDefault();
    const duration = parseInt(minutes, 10);
    if (!duration || duration <= 0) {
      setError("Enter how many minutes.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const entry = await logActivity(patientId, type, duration, note.trim() || undefined);
      setLogs([entry, ...logs]);
      setMinutes("");
      setNote("");
    } catch (e: any) {
      setError(e.message || "Failed to log activity");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this activity entry?")) return;
    try {
      await deleteActivity(patientId, id);
      setLogs((prev) => prev.filter((l) => l.id !== id));
    } catch (e: any) {
      setError(e.message || "Failed to delete entry");
    }
  }

  // Daily-total-minutes trend, last 7 days, oldest first.
  const trend = useMemo(() => {
    const days: { key: string; label: string; minutes: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      days.push({ key, label: d.toLocaleDateString(undefined, { weekday: "short" }), minutes: 0 });
    }
    for (const l of logs) {
      const key = dayKey(l.logged_at);
      const day = days.find((d) => d.key === key);
      if (day) day.minutes += l.duration_minutes;
    }
    return days;
  }, [logs]);

  const maxMinutes = Math.max(...trend.map((d) => d.minutes), 30);

  return (
    <SectionCard eyebrow="Daily Tracking" title="Daily activity" icon={<ActivityIcon />} accent="steel">
      {isOwner && (
        <form onSubmit={handleLog} className="mb-5 flex flex-wrap items-end gap-2">
          <div className="flex gap-1">
            {TYPES.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setType(t.value)}
                className={`text-xs px-2.5 py-2 rounded-lg border transition ${
                  type === t.value ? "border-steel bg-steel/10" : "border-sageLight hover:bg-sageLight"
                }`}
              >
                {t.emoji} {t.label}
              </button>
            ))}
          </div>
          <input
            type="number"
            min={1}
            max={1440}
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            placeholder="Minutes"
            className="w-24 border border-sageLight rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
          />
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional note"
            className="flex-1 min-w-[120px] border border-sageLight rounded-lg px-2 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-steel text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
          >
            {loading ? "..." : "Log"}
          </button>
        </form>
      )}
      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      <div className="flex items-end gap-2 h-24 mb-5">
        {trend.map((d) => (
          <div key={d.key} className="flex-1 flex flex-col items-center gap-1">
            <div
              title={`${d.label}: ${d.minutes} min`}
              className="w-full bg-steel/70 rounded-t"
              style={{ height: `${Math.max((d.minutes / maxMinutes) * 72, d.minutes > 0 ? 4 : 0)}px` }}
            />
            <span className="text-[10px] text-ink/40">{d.label}</span>
          </div>
        ))}
      </div>

      {logs.length === 0 ? (
        <p className="text-ink/50 text-sm">No activity logged yet.</p>
      ) : (
        <ul className="space-y-2 max-h-72 overflow-y-auto">
          {logs.map((l) => (
            <li key={l.id} className="flex items-start justify-between border border-sageLight rounded-lg px-3 py-2">
              <div>
                <span className="text-sm font-medium text-ink">
                  {TYPES.find((t) => t.value === l.activity_type)?.emoji} {l.activity_type} · {l.duration_minutes} min
                </span>
                {l.note && <p className="text-xs text-ink/60 mt-0.5">{l.note}</p>}
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <span className="text-xs text-ink/40">{new Date(l.logged_at).toLocaleString()}</span>
                {isOwner && (
                  <button onClick={() => handleDelete(l.id)} className="text-xs text-alert/70 hover:text-alert hover:underline">
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

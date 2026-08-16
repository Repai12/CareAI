"use client";

import { useState } from "react";
import SectionCard from "@/components/SectionCard";
import { ClipboardIcon } from "./icons";
import { VitalsEntryOut, VitalsIn, logVitals, deleteVitals } from "@/lib/api/vitals";

export default function VitalsPanel({
  patientId,
  isOwner,
  initialHistory,
}: {
  patientId: string;
  isOwner: boolean;
  initialHistory: VitalsEntryOut[];
}) {
  const [history, setHistory] = useState(initialHistory);
  const [form, setForm] = useState({ blood_pressure: "", sugar_level: "", heart_rate: "", temperature: "", notes: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const payload: VitalsIn = {
        blood_pressure: form.blood_pressure,
        sugar_level: parseFloat(form.sugar_level),
        heart_rate: parseFloat(form.heart_rate),
        temperature: parseFloat(form.temperature),
        notes: form.notes || undefined,
      };
      const entry = await logVitals(payload);
      setHistory([entry, ...history]);
      setForm({ blood_pressure: "", sugar_level: "", heart_rate: "", temperature: "", notes: "" });
    } catch (e: any) {
      setError(e.message || "Failed to log vitals");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteVitals(id);
      setHistory(history.filter((h) => h.id !== id));
    } catch (e: any) {
      setError(e.message || "Failed to delete");
    }
  }

  return (
    <SectionCard eyebrow="Feature 1 · CRUD" title="Vitals Logging" icon={<ClipboardIcon />} accent="steel">
      {isOwner && (
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2 mb-4">
          <input
            placeholder="Blood pressure (120/80)"
            value={form.blood_pressure}
            onChange={(e) => setForm({ ...form, blood_pressure: e.target.value })}
            className="col-span-2 border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
            required
          />
          <input
            type="number" step="0.1" placeholder="Sugar (mg/dL)"
            value={form.sugar_level}
            onChange={(e) => setForm({ ...form, sugar_level: e.target.value })}
            className="border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
            required
          />
          <input
            type="number" step="0.1" placeholder="Heart rate (bpm)"
            value={form.heart_rate}
            onChange={(e) => setForm({ ...form, heart_rate: e.target.value })}
            className="border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
            required
          />
          <input
            type="number" step="0.1" placeholder="Temperature (°C)"
            value={form.temperature}
            onChange={(e) => setForm({ ...form, temperature: e.target.value })}
            className="border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
            required
          />
          <input
            placeholder="Notes (optional)"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
          />
          <button
            type="submit" disabled={loading}
            className="col-span-2 bg-steel text-white text-sm font-medium px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50 transition"
          >
            {loading ? "Logging..." : "Log reading"}
          </button>
        </form>
      )}

      {error && <p className="text-alert text-sm mb-3">{error}</p>}

      <p className="text-xs uppercase tracking-wide text-ink/40 font-semibold mb-2">History</p>
      {history.length === 0 ? (
        <p className="text-ink/50 text-sm">No vitals logged yet.</p>
      ) : (
        <ul className="space-y-2 max-h-64 overflow-y-auto">
          {history.map((v) => (
            <li
              key={v.id}
              className={`text-sm rounded-lg px-3 py-2 border ${v.is_abnormal ? "border-alert/40 bg-alert/5" : "border-sageLight bg-white"}`}
            >
              <div className="flex justify-between items-start gap-2">
                <div>
                  <span className="font-medium text-ink">BP {v.blood_pressure}</span>
                  <span className="text-ink/60"> · Sugar {v.sugar_level} · HR {v.heart_rate} · {v.temperature}°C</span>
                  {v.is_abnormal && <span className="ml-2 text-xs text-alert font-semibold">ABNORMAL</span>}
                  {v.notes && <p className="text-ink/50 text-xs mt-1">{v.notes}</p>}
                  <p className="text-ink/40 text-xs mt-0.5">{new Date(v.logged_at).toLocaleString()}</p>
                </div>
                {isOwner && (
                  <button onClick={() => handleDelete(v.id)} className="text-ink/30 hover:text-alert text-xs shrink-0">
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

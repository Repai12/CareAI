"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getVisitNotes,
  createVisitNote,
  updateVisitNote,
  archiveVisitNote,
  summarizeVisitNote,
  type VisitNoteOut,
  type VisitNoteInput,
} from "@/lib/api";
import { getMyRole, getMyUserId } from "@/lib/apiClient";
import PatientQaPanel from "@/components/PatientQaPanel";

const EMPTY_NOTE: VisitNoteInput = { visit_date: "", notes: "", prescription: "" };

export default function VisitNotesPage() {
  const params = useParams<{ patientId: string }>();
  const router = useRouter();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [myUserId, setMyUserId] = useState<string | null>(null);
  const [notes, setNotes] = useState<VisitNoteOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_NOTE);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState({ notes: "", prescription: "" });
  const [summarizingId, setSummarizingId] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<Record<string, string>>({});

  function load() {
    setLoading(true);
    getVisitNotes(patientId)
      .then(setNotes)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    setRole(getMyRole());
    setMyUserId(getMyUserId());
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const isDoctor = role === "doctor";

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createVisitNote(patientId, form);
      setNotes((prev) => [created, ...prev]);
      setForm(EMPTY_NOTE);
      setShowForm(false);
    } catch (e: any) {
      setError(e.message || "Couldn't save that note.");
    } finally {
      setSaving(false);
    }
  }

  function startEdit(note: VisitNoteOut) {
    setEditingId(note.id);
    setEditText({ notes: note.notes, prescription: note.prescription || "" });
  }

  async function handleSaveEdit(noteId: string) {
    try {
      const updated = await updateVisitNote(patientId, noteId, editText);
      setNotes((prev) => prev.map((n) => (n.id === noteId ? updated : n)));
      setEditingId(null);
    } catch (e: any) {
      setError(e.message || "Couldn't update that note.");
    }
  }

  async function handleSummarize(noteId: string) {
    setSummarizingId(noteId);
    setSummaryError((prev) => ({ ...prev, [noteId]: "" }));
    try {
      const updated = await summarizeVisitNote(patientId, noteId);
      setNotes((prev) => prev.map((n) => (n.id === noteId ? updated : n)));
    } catch (e: any) {
      setSummaryError((prev) => ({ ...prev, [noteId]: e.message || "AI explanation unavailable right now." }));
    } finally {
      setSummarizingId(null);
    }
  }

  async function handleArchive(noteId: string) {
    if (!confirm("Archive this visit note?")) return;
    try {
      await archiveVisitNote(patientId, noteId);
      setNotes((prev) => prev.filter((n) => n.id !== noteId));
    } catch (e: any) {
      setError(e.message || "Couldn't archive that note.");
    }
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-sm text-sage font-medium">CareAI · Doctor Visit History</p>
          <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Visit notes & prescriptions</h1>
        </div>
        {isDoctor && (
          <button
            onClick={() => setShowForm((s) => !s)}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            {showForm ? "Cancel" : "+ Add visit note"}
          </button>
        )}
      </header>

      {error && <p className="text-alert text-sm mb-4">{error}</p>}
      {loading && <p className="text-ink/50 text-sm">Loading...</p>}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-sageLight rounded-xl p-4 mb-6 space-y-3">
          <div>
            <label className="text-xs text-ink/50">Visit date</label>
            <input
              required
              type="date"
              value={form.visit_date}
              onChange={(e) => setForm({ ...form, visit_date: e.target.value })}
              className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <textarea
            required
            placeholder="Notes"
            rows={3}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
          />
          <textarea
            placeholder="Prescription (optional)"
            rows={2}
            value={form.prescription}
            onChange={(e) => setForm({ ...form, prescription: e.target.value })}
            className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
          />
          <button type="submit" disabled={saving} className="text-xs font-medium bg-sage text-white px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50">
            {saving ? "Saving..." : "Save note"}
          </button>
        </form>
      )}

      {!loading && notes.length === 0 && <p className="text-ink/50 text-sm">No visit notes yet.</p>}

      <ul className="space-y-3">
        {notes.map((note) => {
          const isOwnNote = isDoctor && note.doctor_id === myUserId;
          return (
            <li key={note.id} className="bg-white border border-sageLight rounded-xl p-4">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <p className="font-medium text-ink text-sm">{note.doctor_name}</p>
                  <p className="text-xs text-ink/40">{note.visit_date}</p>
                </div>
                {isOwnNote && editingId !== note.id && (
                  <div className="flex gap-3 shrink-0">
                    <button onClick={() => startEdit(note)} className="text-xs text-sage hover:underline">
                      Edit
                    </button>
                    <button onClick={() => handleArchive(note.id)} className="text-xs text-alert hover:underline">
                      Archive
                    </button>
                  </div>
                )}
              </div>

              {editingId === note.id ? (
                <div className="mt-3 space-y-2">
                  <textarea
                    rows={3}
                    value={editText.notes}
                    onChange={(e) => setEditText({ ...editText, notes: e.target.value })}
                    className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
                  />
                  <textarea
                    rows={2}
                    value={editText.prescription}
                    onChange={(e) => setEditText({ ...editText, prescription: e.target.value })}
                    className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
                  />
                  <div className="flex gap-2">
                    <button onClick={() => handleSaveEdit(note.id)} className="text-xs font-medium bg-sage text-white px-3 py-1.5 rounded-lg hover:bg-sage/90">
                      Save
                    </button>
                    <button onClick={() => setEditingId(null)} className="text-xs text-ink/50 hover:underline">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-sm text-ink mt-2">{note.notes}</p>
                  {note.prescription && <p className="text-xs text-ink/50 mt-1">Rx: {note.prescription}</p>}

                  {note.ai_summary ? (
                    <div className="mt-3 bg-gold/10 border border-gold/30 rounded-lg p-3">
                      <p className="text-xs text-ink/40 italic mb-1">
                        AI-generated explanation, not a diagnosis - review before acting on it.
                      </p>
                      <p className="text-sm text-ink">{note.ai_summary}</p>
                    </div>
                  ) : (
                    <button
                      onClick={() => handleSummarize(note.id)}
                      disabled={summarizingId === note.id}
                      className="text-xs font-medium text-gold border border-gold/30 rounded-full px-3 py-1.5 mt-3 hover:bg-gold/10 disabled:opacity-50 transition"
                    >
                      {summarizingId === note.id ? "Explaining..." : "Explain in plain English"}
                    </button>
                  )}
                  {summaryError[note.id] && <p className="text-alert text-xs mt-1">{summaryError[note.id]}</p>}
                </>
              )}
            </li>
          );
        })}
      </ul>

      {isDoctor && (
        <div className="mt-8">
          <PatientQaPanel patientId={patientId} />
        </div>
      )}

      <button onClick={() => router.back()} className="inline-block mt-8 text-sm text-sage font-medium hover:underline">
        Back
      </button>
    </main>
  );
}

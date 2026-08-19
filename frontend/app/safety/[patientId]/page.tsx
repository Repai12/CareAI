"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getEmergencyContacts,
  addEmergencyContact,
  deleteEmergencyContact,
  getFallHistory,
  logFallIncident,
  checkIn,
  getCheckinHistory,
  getMyConnections,
  type EmergencyContactOut,
  type FallIncidentOut,
  type SafetyCheckinOut,
} from "@/lib/api";
import { getMyRole } from "@/lib/apiClient";

const SEVERITIES = ["minor", "moderate", "severe"];

export default function SafetyPage() {
  const params = useParams<{ patientId: string }>();
  const router = useRouter();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [isSelf, setIsSelf] = useState(false);
  const [canManage, setCanManage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [contacts, setContacts] = useState<EmergencyContactOut[]>([]);
  const [contactForm, setContactForm] = useState({ name: "", phone: "", relationship: "", priority: 1 });
  const [showContactForm, setShowContactForm] = useState(false);

  const [falls, setFalls] = useState<FallIncidentOut[]>([]);
  const [fallForm, setFallForm] = useState({ severity: "minor", details: "" });
  const [showFallForm, setShowFallForm] = useState(false);

  const [checkins, setCheckins] = useState<SafetyCheckinOut[]>([]);
  const [checkinToday, setCheckinToday] = useState(false);

  useEffect(() => {
    const r = getMyRole();
    setRole(r);
    const self = r === "patient";
    setIsSelf(self);

    if (self) {
      setCanManage(true);
      getEmergencyContacts().then(setContacts).catch((e) => setError(e.message));
    } else {
      getMyConnections()
        .then((links) => {
          const link = links.find((l) => l.patient_id === patientId && l.status === "active");
          setCanManage(link?.permission_level === "view_and_manage");
        })
        .catch(() => setCanManage(false));
    }

    getFallHistory(patientId).then(setFalls).catch((e) => setError(e.message));
    getCheckinHistory(patientId)
      .then((history) => {
        setCheckins(history);
        const today = new Date().toDateString();
        setCheckinToday(history.some((c) => new Date(c.checked_in_at).toDateString() === today));
      })
      .catch((e) => setError(e.message));
  }, [patientId]);

  async function handleAddContact(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await addEmergencyContact(contactForm);
      setContacts((prev) => [...prev, created].sort((a, b) => a.priority - b.priority));
      setContactForm({ name: "", phone: "", relationship: "", priority: 1 });
      setShowContactForm(false);
    } catch (e: any) {
      setError(e.message || "Couldn't add that contact.");
    }
  }

  async function handleDeleteContact(id: string) {
    if (!confirm("Remove this emergency contact?")) return;
    try {
      await deleteEmergencyContact(id);
      setContacts((prev) => prev.filter((c) => c.id !== id));
    } catch (e: any) {
      setError(e.message || "Couldn't remove that contact.");
    }
  }

  async function handleLogFall(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await logFallIncident(patientId, fallForm.severity, fallForm.details || undefined);
      setFalls((prev) => [created, ...prev]);
      setFallForm({ severity: "minor", details: "" });
      setShowFallForm(false);
    } catch (e: any) {
      setError(e.message || "Couldn't log that fall.");
    }
  }

  async function handleCheckIn() {
    try {
      const entry = await checkIn();
      setCheckins((prev) => [entry, ...prev]);
      setCheckinToday(true);
    } catch (e: any) {
      setError(e.message || "Couldn't record check-in.");
    }
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-6">
        <p className="text-sm text-sage font-medium">CareAI · Safety</p>
        <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Emergency contacts, falls & check-ins</h1>
      </header>

      {error && <p className="text-alert text-sm mb-4">{error}</p>}

      {/* Daily check-in */}
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-ink/70 mb-3">Daily check-in</h2>
        {isSelf && (
          <button
            onClick={handleCheckIn}
            disabled={checkinToday}
            className="bg-sage text-white font-bold py-3 px-6 rounded-xl shadow-sm hover:opacity-90 disabled:opacity-50 transition mb-3"
          >
            {checkinToday ? "✓ Checked in today" : "I'm okay - check in"}
          </button>
        )}
        {checkins.length === 0 ? (
          <p className="text-ink/50 text-sm">No check-ins yet.</p>
        ) : (
          <p className="text-xs text-ink/50">Last check-in: {new Date(checkins[0].checked_in_at).toLocaleString()}</p>
        )}
      </section>

      {/* Emergency contacts - patient-only, backend has no family/doctor management path */}
      {isSelf && (
        <section className="mb-10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-ink/70">Emergency contacts</h2>
            <button
              onClick={() => setShowContactForm((s) => !s)}
              className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
            >
              {showContactForm ? "Cancel" : "+ Add contact"}
            </button>
          </div>

          {contacts.length === 0 && (
            <p className="text-xs text-alert bg-alert/10 rounded-lg px-3 py-2 mb-3">
              No emergency contacts yet - SOS won't be able to text anyone until you add one.
            </p>
          )}

          {showContactForm && (
            <form onSubmit={handleAddContact} className="bg-white border border-sageLight rounded-xl p-4 mb-3 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input required placeholder="Name" value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  className="border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <input required placeholder="Phone (e.g. +15551234567)" value={contactForm.phone}
                  onChange={(e) => setContactForm({ ...contactForm, phone: e.target.value })}
                  className="border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <input required placeholder="Relationship (e.g. Daughter)" value={contactForm.relationship}
                  onChange={(e) => setContactForm({ ...contactForm, relationship: e.target.value })}
                  className="border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <div>
                  <label className="text-xs text-ink/50">Priority (1 = contacted first)</label>
                  <input type="number" min={1} value={contactForm.priority}
                    onChange={(e) => setContactForm({ ...contactForm, priority: Number(e.target.value) })}
                    className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <button type="submit" className="text-xs font-medium bg-sage text-white px-4 py-2 rounded-lg hover:bg-sage/90">
                Save contact
              </button>
            </form>
          )}

          {contacts.length > 0 && (
            <ul className="space-y-2">
              {contacts.map((c) => (
                <li key={c.id} className="bg-white border border-sageLight rounded-xl p-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-ink text-sm">
                      {c.name} <span className="text-ink/40 font-normal">· {c.relationship}</span>
                    </p>
                    <p className="text-xs text-ink/50 mt-0.5">{c.phone} · priority {c.priority}</p>
                  </div>
                  <button onClick={() => handleDeleteContact(c.id)} className="text-xs text-alert hover:underline shrink-0">
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {/* Fall incident log */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-ink/70">Fall log</h2>
          {canManage && (
            <button
              onClick={() => setShowFallForm((s) => !s)}
              className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
            >
              {showFallForm ? "Cancel" : "+ Log a fall"}
            </button>
          )}
        </div>

        {showFallForm && (
          <form onSubmit={handleLogFall} className="bg-white border border-sageLight rounded-xl p-4 mb-3 space-y-3">
            <select
              value={fallForm.severity}
              onChange={(e) => setFallForm({ ...fallForm, severity: e.target.value })}
              className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s[0].toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
            <textarea
              placeholder="What happened? (optional)"
              value={fallForm.details}
              onChange={(e) => setFallForm({ ...fallForm, details: e.target.value })}
              className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm"
              rows={2}
            />
            <button type="submit" className="text-xs font-medium bg-alert text-white px-4 py-2 rounded-lg hover:opacity-90">
              Log fall
            </button>
          </form>
        )}

        {falls.length === 0 ? (
          <p className="text-ink/50 text-sm">No falls logged.</p>
        ) : (
          <ul className="space-y-2">
            {falls.map((f) => (
              <li key={f.id} className="bg-white border border-sageLight rounded-xl p-4">
                <p className="text-sm text-ink">
                  <span className="font-medium capitalize">{f.severity}</span> · {new Date(f.occurred_at).toLocaleString()}
                </p>
                {f.details && <p className="text-xs text-ink/50 mt-1">{f.details}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <button onClick={() => router.back()} className="inline-block mt-8 text-sm text-sage font-medium hover:underline">
        Back
      </button>
    </main>
  );
}

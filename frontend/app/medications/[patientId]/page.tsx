"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getMedications,
  createMedication,
  deleteMedication,
  getAppointments,
  bookAppointment,
  cancelAppointment,
  getMyConnections,
  type MedicationOut,
  type MedicationInput,
  type AppointmentDetail,
  type AppointmentInput,
} from "@/lib/api";
import { getMyRole } from "@/lib/apiClient";

const EMPTY_MED: MedicationInput = { medicine_name: "", dosage: "", frequency: "", start_date: "", end_date: "" };
const EMPTY_APPT: AppointmentInput = { doctor_name: "", appointment_date: "", start_time: "", end_time: "", reason: "", location: "" };

export default function MedicationsAppointmentsPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [medications, setMedications] = useState<MedicationOut[]>([]);
  const [appointments, setAppointments] = useState<AppointmentDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [medForm, setMedForm] = useState(EMPTY_MED);
  const [showMedForm, setShowMedForm] = useState(false);
  const [apptForm, setApptForm] = useState(EMPTY_APPT);
  const [showApptForm, setShowApptForm] = useState(false);
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    Promise.all([getMedications(patientId), getAppointments(patientId)])
      .then(([meds, appts]) => {
        setMedications(meds);
        setAppointments(appts);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const r = getMyRole();
    setRole(r);
    if (r === "patient") {
      setCanManage(true);
    } else {
      getMyConnections()
        .then((links) => {
          const link = links.find((l) => l.patient_id === patientId && l.status === "active");
          setCanManage(link?.permission_level === "view_and_manage");
        })
        .catch(() => setCanManage(false));
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  async function handleAddMedication(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createMedication(patientId, {
        ...medForm,
        start_date: medForm.start_date || null,
        end_date: medForm.end_date || null,
      });
      setMedications((prev) => [created, ...prev]);
      setMedForm(EMPTY_MED);
      setShowMedForm(false);
    } catch (e: any) {
      setError(e.message || "Couldn't add that medication.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteMedication(id: string) {
    if (!confirm("Remove this medication?")) return;
    try {
      await deleteMedication(patientId, id);
      setMedications((prev) => prev.filter((m) => m.id !== id));
    } catch (e: any) {
      setError(e.message || "Couldn't remove that medication.");
    }
  }

  async function handleBookAppointment(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await bookAppointment(patientId, apptForm);
      setAppointments((prev) => [...prev, created]);
      setApptForm(EMPTY_APPT);
      setShowApptForm(false);
    } catch (e: any) {
      setError(e.message || "Couldn't book that appointment.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCancelAppointment(id: string) {
    if (!confirm("Cancel this appointment?")) return;
    try {
      await cancelAppointment(patientId, id);
      setAppointments((prev) => prev.filter((a) => a.id !== id));
    } catch (e: any) {
      setError(e.message || "Couldn't cancel that appointment.");
    }
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-6">
        <p className="text-sm text-sage font-medium">CareAI · Medications & Appointments</p>
        <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Care plan</h1>
      </header>

      {error && <p className="text-alert text-sm mb-4">{error}</p>}
      {loading && <p className="text-ink/50 text-sm">Loading...</p>}

      {!loading && (
        <>
          {/* Medications */}
          <section className="mb-10">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-ink/70">Medications</h2>
              {canManage && (
                <button
                  onClick={() => setShowMedForm((s) => !s)}
                  className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
                >
                  {showMedForm ? "Cancel" : "+ Add medication"}
                </button>
              )}
            </div>

            {showMedForm && (
              <form onSubmit={handleAddMedication} className="bg-white border border-sageLight rounded-xl p-4 mb-3 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input required placeholder="Medicine name" value={medForm.medicine_name}
                    onChange={(e) => setMedForm({ ...medForm, medicine_name: e.target.value })}
                    className="border border-sageLight rounded-lg px-3 py-2 text-sm col-span-2" />
                  <input required placeholder="Dosage (e.g. 500mg)" value={medForm.dosage}
                    onChange={(e) => setMedForm({ ...medForm, dosage: e.target.value })}
                    className="border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  <input required placeholder="Frequency (e.g. Twice daily)" value={medForm.frequency}
                    onChange={(e) => setMedForm({ ...medForm, frequency: e.target.value })}
                    className="border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  <div>
                    <label className="text-xs text-ink/50">Start date</label>
                    <input type="date" value={medForm.start_date || ""}
                      onChange={(e) => setMedForm({ ...medForm, start_date: e.target.value })}
                      className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-ink/50">End date (optional)</label>
                    <input type="date" value={medForm.end_date || ""}
                      onChange={(e) => setMedForm({ ...medForm, end_date: e.target.value })}
                      className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  </div>
                </div>
                <button type="submit" disabled={saving} className="text-xs font-medium bg-sage text-white px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50">
                  {saving ? "Saving..." : "Save medication"}
                </button>
              </form>
            )}

            {medications.length === 0 ? (
              <p className="text-ink/50 text-sm">No medications on file.</p>
            ) : (
              <ul className="space-y-2">
                {medications.map((m) => (
                  <li key={m.id} className="bg-white border border-sageLight rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-ink text-sm">{m.medicine_name}</p>
                      <p className="text-xs text-ink/50 mt-0.5">
                        {m.dosage} · {m.frequency}
                        {m.end_date && ` · until ${m.end_date}`}
                      </p>
                    </div>
                    {canManage && (
                      <button onClick={() => handleDeleteMedication(m.id)} className="text-xs text-alert hover:underline shrink-0">
                        Remove
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Appointments */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-ink/70">Appointments</h2>
              {canManage && (
                <button
                  onClick={() => setShowApptForm((s) => !s)}
                  className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
                >
                  {showApptForm ? "Cancel" : "+ Book appointment"}
                </button>
              )}
            </div>

            {showApptForm && (
              <form onSubmit={handleBookAppointment} className="bg-white border border-sageLight rounded-xl p-4 mb-3 space-y-3">
                <input required placeholder="Doctor name" value={apptForm.doctor_name}
                  onChange={(e) => setApptForm({ ...apptForm, doctor_name: e.target.value })}
                  className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs text-ink/50">Date</label>
                    <input required type="date" value={apptForm.appointment_date}
                      onChange={(e) => setApptForm({ ...apptForm, appointment_date: e.target.value })}
                      className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-ink/50">Start</label>
                    <input required type="time" value={apptForm.start_time}
                      onChange={(e) => setApptForm({ ...apptForm, start_time: e.target.value })}
                      className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="text-xs text-ink/50">End</label>
                    <input required type="time" value={apptForm.end_time}
                      onChange={(e) => setApptForm({ ...apptForm, end_time: e.target.value })}
                      className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                  </div>
                </div>
                <input placeholder="Location (optional)" value={apptForm.location}
                  onChange={(e) => setApptForm({ ...apptForm, location: e.target.value })}
                  className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <input placeholder="Reason (optional)" value={apptForm.reason}
                  onChange={(e) => setApptForm({ ...apptForm, reason: e.target.value })}
                  className="w-full border border-sageLight rounded-lg px-3 py-2 text-sm" />
                <button type="submit" disabled={saving} className="text-xs font-medium bg-sage text-white px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50">
                  {saving ? "Booking..." : "Book appointment"}
                </button>
              </form>
            )}

            {appointments.length === 0 ? (
              <p className="text-ink/50 text-sm">No appointments booked.</p>
            ) : (
              <ul className="space-y-2">
                {appointments.map((a) => (
                  <li key={a.id} className="bg-white border border-sageLight rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-ink text-sm">{a.doctor_name}</p>
                      <p className="text-xs text-ink/50 mt-0.5">
                        {a.appointment_date} · {a.start_time}–{a.end_time}
                        {a.location && ` · ${a.location}`}
                      </p>
                      {a.reason && <p className="text-xs text-ink/40 mt-0.5">{a.reason}</p>}
                    </div>
                    {canManage && (
                      <button onClick={() => handleCancelAppointment(a.id)} className="text-xs text-alert hover:underline shrink-0">
                        Cancel
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}

      <Link href={`/dashboard/${patientId}`} className="inline-block mt-8 text-sm text-sage font-medium hover:underline">
        Back to dashboard
      </Link>
    </main>
  );
}

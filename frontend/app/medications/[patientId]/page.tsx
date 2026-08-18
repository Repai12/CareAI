"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import MedicationForm from "@/components/MedicationForm";
import MedicationTable from "@/components/MedicationTable";
import AppointmentForm from "@/components/AppointmentForm";
import AppointmentTable from "@/components/AppointmentTable";
import VisitNoteForm from "@/components/VisitNoteForm";
import VisitHistory from "@/components/VisitHistory";
import LogoutButton from "@/components/LogoutButton";
import { Medication, MedicationFormData } from "@/types/medication";
import { Appointment, AppointmentFormData } from "@/types/appointment";
import { VisitNote, VisitNoteCreate } from "@/types/visitNote";
import { getDashboard } from "@/lib/api";
import {
  getMedications,
  addMedication,
  updateMedication,
  deleteMedication,
  getAppointments,
  addAppointment,
  updateAppointment,
  deleteAppointment,
  getVisitNotes,
  addVisitNote,
} from "@/services/api";

const emptyMedicationForm: MedicationFormData = {
  medicine_name: "",
  dosage: "",
  frequency: "",
  start_date: "",
  end_date: "",
};

const emptyAppointmentForm: AppointmentFormData = {
  patient_name: "",
  patient_email: "",
  doctor_name: "",
  appointment_date: "",
  start_time: "",
  end_time: "",
  reason: "",
  location: "",
};

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function MedicationsPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [patient, setPatient] = useState<{ name: string; email: string } | null>(null);
  const [role, setRole] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [accessError, setAccessError] = useState<string | null>(null);

  const [medications, setMedications] = useState<Medication[]>([]);
  const [medLoading, setMedLoading] = useState(true);
  const [medForm, setMedForm] = useState(emptyMedicationForm);
  const [editingMedId, setEditingMedId] = useState<string | null>(null);

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [apptLoading, setApptLoading] = useState(true);
  const [apptForm, setApptForm] = useState(emptyAppointmentForm);
  const [editingApptId, setEditingApptId] = useState<string | null>(null);

  const [visitNotes, setVisitNotes] = useState<VisitNote[]>([]);

  const canEdit = role === "patient" || role === "doctor";

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;

    getDashboard(patientId)
      .then((d) => {
        setPatient({ name: d.patient.name, email: d.patient.email });
        setApptForm((f) => ({ ...f, patient_name: d.patient.name, patient_email: d.patient.email }));
      })
      .catch((e) => setAccessError(e.message));

    refreshMedications();
    refreshAppointments();
  }, [patientId]);

  useEffect(() => {
    if (patient) refreshVisitNotes(patient.name);
  }, [patient]);

  function refreshMedications() {
    setMedLoading(true);
    getMedications(patientId)
      .then(setMedications)
      .catch((e) => setError(e?.response?.data?.detail || e.message))
      .finally(() => setMedLoading(false));
  }

  function refreshAppointments() {
    setApptLoading(true);
    getAppointments(patientId)
      .then(setAppointments)
      .catch((e) => setError(e?.response?.data?.detail || e.message))
      .finally(() => setApptLoading(false));
  }

  function refreshVisitNotes(patientName: string) {
    getVisitNotes(patientName)
      .then(setVisitNotes)
      .catch((e) => setError(e?.response?.data?.detail || e.message));
  }

  async function handleMedicationSubmit() {
    setError(null);
    try {
      if (editingMedId) {
        await updateMedication(editingMedId, medForm);
      } else {
        await addMedication(patientId, medForm);
      }
      setMedForm(emptyMedicationForm);
      setEditingMedId(null);
      refreshMedications();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to save medication");
    }
  }

  async function handleMedicationDelete(id: string) {
    setError(null);
    try {
      await deleteMedication(id);
      refreshMedications();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to delete medication");
    }
  }

  async function handleAppointmentSubmit() {
    setError(null);
    try {
      if (editingApptId) {
        await updateAppointment(editingApptId, apptForm);
      } else {
        await addAppointment(apptForm);
      }
      setApptForm({ ...emptyAppointmentForm, patient_name: patient?.name || "", patient_email: patient?.email || "" });
      setEditingApptId(null);
      refreshAppointments();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to save appointment");
    }
  }

  async function handleAppointmentDelete(id: string) {
    setError(null);
    try {
      await deleteAppointment(id);
      refreshAppointments();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to delete appointment");
    }
  }

  async function handleVisitNoteCreated(note: VisitNoteCreate) {
    setError(null);
    try {
      await addVisitNote(note);
      if (patient) refreshVisitNotes(patient.name);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to save visit note");
    }
  }

  if (accessError) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-paper">
        <p className="text-alert">{accessError}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-5xl mx-auto bg-paper">
      <header className="mb-2 flex items-start justify-between flex-wrap gap-3">
        <div>
          <p className="text-sm text-sage font-medium">CareAI · Medications Module (Member 2)</p>
          <h1 className="text-3xl font-display font-bold text-ink mt-0.5">
            {patient ? `${patient.name}'s Medications & Appointments` : "Medications, Appointments & Visit History"}
          </h1>
          {patient && <p className="text-ink/50 text-sm">{patient.email}</p>}
          {!canEdit && role && (
            <p className="text-xs text-gold mt-1">Viewing as {role} — read-only, editing is restricted to the patient or their doctor.</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Link
            href={`/dashboard/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            ← Dashboard
          </Link>
          <LogoutButton />
        </div>
      </header>

      {error && <p className="text-alert text-sm my-3">{error}</p>}

      <section className="mt-8">
        <h2 className="text-xl font-display font-semibold text-ink mb-3">Medications (current &amp; previous)</h2>
        <div className={canEdit ? "grid md:grid-cols-2 gap-6" : "grid gap-6"}>
          {canEdit && (
            <MedicationForm
              formData={medForm}
              setFormData={setMedForm}
              onSubmit={handleMedicationSubmit}
              editing={!!editingMedId}
              onCancel={() => {
                setMedForm(emptyMedicationForm);
                setEditingMedId(null);
              }}
            />
          )}
          <MedicationTable
            medications={medications}
            loading={medLoading}
            readOnly={!canEdit}
            onEdit={(m) => {
              if (!canEdit) return;
              setEditingMedId(m.id);
              setMedForm({
                medicine_name: m.medicine_name,
                dosage: m.dosage,
                frequency: m.frequency,
                start_date: m.start_date || "",
                end_date: m.end_date || "",
              });
            }}
            onDelete={canEdit ? handleMedicationDelete : () => {}}
          />
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-xl font-display font-semibold text-ink mb-3">Appointments</h2>
        <div className={canEdit ? "grid md:grid-cols-2 gap-6" : "grid gap-6"}>
          {canEdit && (
            <AppointmentForm
              formData={apptForm}
              setFormData={setApptForm}
              onSubmit={handleAppointmentSubmit}
              editing={!!editingApptId}
              onCancel={() => {
                setApptForm({ ...emptyAppointmentForm, patient_name: patient?.name || "", patient_email: patient?.email || "" });
                setEditingApptId(null);
              }}
            />
          )}
          <AppointmentTable
            appointments={appointments}
            loading={apptLoading}
            readOnly={!canEdit}
            onEdit={(a) => {
              if (!canEdit) return;
              setEditingApptId(a.id);
              setApptForm({
                patient_name: a.patient_name,
                patient_email: a.patient_email,
                doctor_name: a.doctor_name,
                appointment_date: a.appointment_date,
                start_time: a.start_time,
                end_time: a.end_time,
                reason: a.reason || "",
                location: a.location || "",
              });
            }}
            onDelete={canEdit ? handleAppointmentDelete : () => {}}
          />
        </div>
      </section>

      <section className="mt-10 mb-10">
        <h2 className="text-xl font-display font-semibold text-ink mb-3">Doctor Visit History</h2>
        <div className={canEdit ? "grid md:grid-cols-2 gap-6" : "grid gap-6"}>
          {canEdit && (
            <VisitNoteForm
              onCreated={handleVisitNoteCreated}
              initialPatientName={patient?.name || ""}
            />
          )}
          <VisitHistory notes={visitNotes} />
        </div>
      </section>
    </main>
  );
}

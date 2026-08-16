"use client";

import { FormEvent, useState } from "react";
import { VisitNoteCreate } from "../types/visitNote";

interface VisitNoteFormProps {
  onCreated?: (note: VisitNoteCreate) => void;
  initialPatientName?: string;
  initialDoctorName?: string;
  initialAppointmentId?: number | null;
}

export default function VisitNoteForm({
  onCreated,
  initialPatientName = "",
  initialDoctorName = "",
  initialAppointmentId = null,
}: VisitNoteFormProps) {
  const [patientName, setPatientName] = useState(initialPatientName);
  const [doctorName, setDoctorName] = useState(initialDoctorName);
  const [appointmentId, setAppointmentId] = useState(
    initialAppointmentId?.toString() || ""
  );
  const [visitDate, setVisitDate] = useState("");
  const [notes, setNotes] = useState("");
  const [prescription, setPrescription] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setMessage("");
    setError("");

    if (!patientName.trim()) {
      setError("Please enter the patient's name.");
      return;
    }

    if (!doctorName.trim()) {
      setError("Please enter the doctor's name.");
      return;
    }

    if (!visitDate) {
      setError("Please select the visit date.");
      return;
    }

    if (!notes.trim()) {
      setError("Please enter the consultation notes.");
      return;
    }

    // Prevent selecting a future visit date.
    const selectedDate = new Date(`${visitDate}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    if (selectedDate > today) {
      setError("Visit date cannot be in the future.");
      return;
    }

    const note: VisitNoteCreate = {
      patient_name: patientName.trim(),
      doctor_name: doctorName.trim(),
      appointment_id: appointmentId
        ? Number(appointmentId)
        : null,
      visit_date: visitDate,
      notes: notes.trim(),
      prescription: prescription.trim() || null,
    };

    if (onCreated) {
      onCreated(note);
    }

    setMessage("Visit note is ready to be saved.");

    setPatientName("");
    setDoctorName("");
    setAppointmentId("");
    setVisitDate("");
    setNotes("");
    setPrescription("");
  };

  return (
    <div className="w-full max-w-2xl rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-2 text-2xl font-semibold text-gray-800">
        Add Visit Note
      </h2>

      <p className="mb-6 text-sm text-gray-500">
        Record consultation details and prescription information.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Patient Name */}
        <div>
          <label
            htmlFor="patientName"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Patient Name
          </label>

          <input
            id="patientName"
            type="text"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
            placeholder="Enter patient name"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Doctor Name */}
        <div>
          <label
            htmlFor="doctorName"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Doctor Name
          </label>

          <input
            id="doctorName"
            type="text"
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            placeholder="Enter doctor name"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Appointment ID */}
        <div>
          <label
            htmlFor="appointmentId"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Appointment ID
          </label>

          <input
            id="appointmentId"
            type="number"
            min="1"
            value={appointmentId}
            onChange={(e) => setAppointmentId(e.target.value)}
            placeholder="Optional"
            className="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />

          <p className="mt-1 text-xs text-gray-500">
            Leave empty if this visit is not connected to an appointment.
          </p>
        </div>

        {/* Visit Date */}
        <div>
          <label
            htmlFor="visitDate"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Visit Date
          </label>

          <input
            id="visitDate"
            type="date"
            value={visitDate}
            max={new Date().toISOString().split("T")[0]}
            onChange={(e) => setVisitDate(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Consultation Notes */}
        <div>
          <label
            htmlFor="notes"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Consultation Notes
          </label>

          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter consultation notes..."
            rows={5}
            className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Prescription */}
        <div>
          <label
            htmlFor="prescription"
            className="mb-1 block text-sm font-medium text-gray-700"
          >
            Prescription
          </label>

          <textarea
            id="prescription"
            value={prescription}
            onChange={(e) => setPrescription(e.target.value)}
            placeholder="Enter prescription information (optional)..."
            rows={4}
            className="w-full resize-y rounded-lg border border-gray-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Success */}
        {message && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
            {message}
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          className="w-full rounded-lg bg-blue-600 px-4 py-2.5 font-medium text-white transition hover:bg-blue-700"
        >
          Save Visit Note
        </button>
      </form>
    </div>
  );
}
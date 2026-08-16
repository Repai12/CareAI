"use client";

import { useState } from "react";
import { VisitNote } from "../types/visitNote";

interface VisitHistoryProps {
  notes?: VisitNote[];
}

export default function VisitHistory({
  notes = [],
}: VisitHistoryProps) {
  const [selectedNote, setSelectedNote] = useState<VisitNote | null>(null);

  if (notes.length === 0) {
    return (
      <div className="w-full rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-2 text-2xl font-semibold text-gray-800">
          Visit History
        </h2>

        <p className="text-sm text-gray-500">
          No visit records are available yet.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">
          Visit History
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          View previous medical consultations and prescriptions.
        </p>
      </div>

      <div className="space-y-4">
        {notes.map((note) => (
          <div
            key={note.id}
            className="rounded-lg border border-gray-200 p-4 transition hover:shadow-sm"
          >
            <div className="flex flex-col justify-between gap-3 sm:flex-row">
              <div>
                <h3 className="font-semibold text-gray-800">
                  Dr. {note.doctor_name}
                </h3>

                <p className="text-sm text-gray-500">
                  Patient: {note.patient_name}
                </p>

                <p className="mt-1 text-sm text-gray-500">
                  Visit Date:{" "}
                  {new Date(
                    `${note.visit_date}T00:00:00`
                  ).toLocaleDateString()}
                </p>
              </div>

              <span
                className={`h-fit rounded-full px-3 py-1 text-xs font-medium ${
                  note.status === "active"
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {note.status}
              </span>
            </div>

            <div className="mt-4">
              <p className="line-clamp-2 text-sm text-gray-600">
                {note.notes}
              </p>
            </div>

            <div className="mt-4">
              <button
                type="button"
                onClick={() => setSelectedNote(note)}
                className="rounded-lg border border-blue-600 px-4 py-2 text-sm font-medium text-blue-600 transition hover:bg-blue-50"
              >
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Details Modal */}
      {selectedNote && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h3 className="text-2xl font-semibold text-gray-800">
                  Visit Details
                </h3>

                <p className="mt-1 text-sm text-gray-500">
                  Medical consultation record
                </p>
              </div>

              <button
                type="button"
                onClick={() => setSelectedNote(null)}
                className="rounded-lg px-3 py-2 text-gray-500 hover:bg-gray-100 hover:text-gray-800"
              >
                ✕
              </button>
            </div>

            {/* Basic Information */}
            <div className="mb-6 grid gap-4 rounded-lg bg-gray-50 p-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium uppercase text-gray-500">
                  Patient
                </p>

                <p className="mt-1 font-medium text-gray-800">
                  {selectedNote.patient_name}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium uppercase text-gray-500">
                  Doctor
                </p>

                <p className="mt-1 font-medium text-gray-800">
                  Dr. {selectedNote.doctor_name}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium uppercase text-gray-500">
                  Visit Date
                </p>

                <p className="mt-1 font-medium text-gray-800">
                  {new Date(
                    `${selectedNote.visit_date}T00:00:00`
                  ).toLocaleDateString()}
                </p>
              </div>

              <div>
                <p className="text-xs font-medium uppercase text-gray-500">
                  Status
                </p>

                <p className="mt-1 font-medium capitalize text-gray-800">
                  {selectedNote.status}
                </p>
              </div>

              {selectedNote.appointment_id !== null && (
                <div>
                  <p className="text-xs font-medium uppercase text-gray-500">
                    Appointment ID
                  </p>

                  <p className="mt-1 font-medium text-gray-800">
                    {selectedNote.appointment_id}
                  </p>
                </div>
              )}
            </div>

            {/* Consultation Notes */}
            <div className="mb-6">
              <h4 className="mb-2 text-lg font-semibold text-gray-800">
                Consultation Notes
              </h4>

              <div className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-white p-4 text-sm leading-6 text-gray-700">
                {selectedNote.notes}
              </div>
            </div>

            {/* Prescription */}
            <div className="mb-6">
              <h4 className="mb-2 text-lg font-semibold text-gray-800">
                Prescription
              </h4>

              <div className="whitespace-pre-wrap rounded-lg border border-gray-200 bg-white p-4 text-sm leading-6 text-gray-700">
                {selectedNote.prescription || "No prescription recorded."}
              </div>
            </div>

            {/* Timestamps */}
            <div className="border-t border-gray-200 pt-4 text-xs text-gray-500">
              <p>
                Created:{" "}
                {new Date(
                  selectedNote.created_at
                ).toLocaleString()}
              </p>

              <p className="mt-1">
                Last updated:{" "}
                {new Date(
                  selectedNote.updated_at
                ).toLocaleString()}
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedNote(null)}
                className="rounded-lg bg-gray-800 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-900"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"use client";

import { Medication } from "../types/medication";

interface MedicationTableProps {
  medications: Medication[];
  loading: boolean;
  onEdit: (medication: Medication) => void;
  onDelete: (id: string) => void;
  readOnly?: boolean;
}

export default function MedicationTable({
  medications,
  loading,
  onEdit,
  onDelete,
  readOnly = false,
}: MedicationTableProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
        <p className="text-gray-500 text-lg">
          Loading medications...
        </p>
      </div>
    );
  }

  if (medications.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
        <h2 className="text-2xl font-bold mb-4">
          Current Medications
        </h2>

        <p className="text-gray-500">
          No medications found.
        </p>

        <p className="text-gray-400 mt-2">
          Add your first medication above.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl p-8">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">
        Current Medications
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-300">
          <thead>
            <tr className="bg-blue-700 text-white">
              <th className="border p-3">ID</th>
              <th className="border p-3">Medicine</th>
              <th className="border p-3">Dosage</th>
              <th className="border p-3">Frequency</th>
              <th className="border p-3">Start Date</th>
              <th className="border p-3">End Date</th>
              {!readOnly && <th className="border p-3">Actions</th>}
            </tr>
          </thead>

          <tbody>
            {medications.map((medication) => (
              <tr
                key={medication.id}
                className="hover:bg-blue-50"
              >
                <td className="border p-3 text-center">
                  {medication.id}
                </td>

                <td className="border p-3">
                  {medication.medicine_name}
                </td>

                <td className="border p-3">
                  {medication.dosage}
                </td>

                <td className="border p-3">
                  {medication.frequency}
                </td>

                <td className="border p-3">
                  {medication.start_date ?? "—"}
                </td>

                <td className="border p-3">
                  {medication.end_date ?? "—"}
                </td>

                {!readOnly && (
                  <td className="border p-3">
                    <div className="flex justify-center gap-2">
                      <button
                        type="button"
                        onClick={() => onEdit(medication)}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg"
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        onClick={() => onDelete(medication.id)}
                        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
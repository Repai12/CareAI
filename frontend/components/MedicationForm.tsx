"use client";

import { MedicationFormData } from "../types/medication";

interface MedicationFormProps {
  formData: MedicationFormData;
  setFormData: React.Dispatch<
    React.SetStateAction<MedicationFormData>
  >;
  onSubmit: () => void;
  editing: boolean;
  onCancel: () => void;
}

export default function MedicationForm({
  formData,
  setFormData,
  onSubmit,
  editing,
  onCancel,
}: MedicationFormProps) {

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  }

  function handleSubmit(
    e: React.FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();
    onSubmit();
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-2xl shadow-xl p-8 mb-8"
    >

      <h2 className="text-3xl font-bold text-blue-700 mb-6">
        {editing
          ? "Edit Medication"
          : "Add New Medication"}
      </h2>

      <div className="grid md:grid-cols-2 gap-6">

        {/* Medicine Name */}
        <div>
          <label className="block font-semibold mb-2">
            Medicine Name
          </label>

          <input
            type="text"
            name="medicine_name"
            value={formData.medicine_name}
            onChange={handleChange}
            placeholder="Paracetamol"
            required
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* Dosage */}
        <div>
          <label className="block font-semibold mb-2">
            Dosage
          </label>

          <input
            type="text"
            name="dosage"
            value={formData.dosage}
            onChange={handleChange}
            placeholder="500mg"
            required
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* Frequency */}
        <div>
          <label className="block font-semibold mb-2">
            Frequency
          </label>

          <input
            type="text"
            name="frequency"
            value={formData.frequency}
            onChange={handleChange}
            placeholder="Twice Daily"
            required
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* Start Date */}
        <div>
          <label className="block font-semibold mb-2">
            Start Date
          </label>

          <input
            type="date"
            name="start_date"
            value={formData.start_date}
            onChange={handleChange}
            required
            className="w-full border rounded-lg p-3"
          />
        </div>

        {/* End Date */}
        <div>
          <label className="block font-semibold mb-2">
            End Date
          </label>

          <input
            type="date"
            name="end_date"
            value={formData.end_date}
            onChange={handleChange}
            required
            className="w-full border rounded-lg p-3"
          />
        </div>

      </div>

      {/* Buttons */}
      <div className="mt-8 flex gap-4">

        <button
          type="submit"
          className={`px-8 py-3 rounded-lg text-white font-semibold transition ${
            editing
              ? "bg-green-600 hover:bg-green-700"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {editing
            ? "Update Medication"
            : "Add Medication"}
        </button>

        {editing && (
          <button
            type="button"
            onClick={onCancel}
            className="px-8 py-3 rounded-lg bg-gray-500 hover:bg-gray-600 text-white font-semibold"
          >
            Cancel
          </button>
        )}

      </div>

    </form>
  );
}
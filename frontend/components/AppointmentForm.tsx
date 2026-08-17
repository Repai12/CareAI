"use client";

import { AppointmentFormData } from "../types/appointment";

interface AppointmentFormProps {
  formData: AppointmentFormData;
  setFormData: React.Dispatch<
    React.SetStateAction<AppointmentFormData>
  >;
  onSubmit: () => void;
  editing: boolean;
  onCancel: () => void;
}

export default function AppointmentForm({
  formData,
  setFormData,
  onSubmit,
  editing,
  onCancel,
}: AppointmentFormProps) {

  function handleChange(
    field: keyof AppointmentFormData,
    value: string
  ) {
    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
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
      className="bg-white rounded-xl shadow-md p-6 mb-8"
    >

      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        {editing
          ? "Edit Appointment"
          : "Create Appointment"}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

        {/* Patient Name */}
        <div>
          <label
            htmlFor="patient_name"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Patient Name
          </label>

          <input
            id="patient_name"
            type="text"
            value={formData.patient_name}
            onChange={(e) =>
              handleChange(
                "patient_name",
                e.target.value
              )
            }
            placeholder="Enter patient name"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Patient Email */}
        <div>
          <label
            htmlFor="patient_email"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Patient Email
          </label>

          <input
            id="patient_email"
            type="email"
            value={formData.patient_email}
            onChange={(e) =>
              handleChange(
                "patient_email",
                e.target.value
              )
            }
            placeholder="Enter patient email"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Doctor Name */}
        <div>
          <label
            htmlFor="doctor_name"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Doctor Name
          </label>

          <input
            id="doctor_name"
            type="text"
            value={formData.doctor_name}
            onChange={(e) =>
              handleChange(
                "doctor_name",
                e.target.value
              )
            }
            placeholder="Enter doctor name"
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Appointment Date */}
        <div>
          <label
            htmlFor="appointment_date"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Appointment Date
          </label>

          <input
            id="appointment_date"
            type="date"
            value={formData.appointment_date}
            onChange={(e) =>
              handleChange(
                "appointment_date",
                e.target.value
              )
            }
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Start Time */}
        <div>
          <label
            htmlFor="start_time"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Start Time
          </label>

          <input
            id="start_time"
            type="time"
            value={formData.start_time}
            onChange={(e) =>
              handleChange(
                "start_time",
                e.target.value
              )
            }
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* End Time */}
        <div>
          <label
            htmlFor="end_time"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            End Time
          </label>

          <input
            id="end_time"
            type="time"
            value={formData.end_time}
            onChange={(e) =>
              handleChange(
                "end_time",
                e.target.value
              )
            }
            required
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Location */}
        <div>
          <label
            htmlFor="location"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Location
          </label>

          <input
            id="location"
            type="text"
            value={formData.location}
            onChange={(e) =>
              handleChange(
                "location",
                e.target.value
              )
            }
            placeholder="Enter appointment location"
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Reason */}
        <div className="md:col-span-2">

          <label
            htmlFor="reason"
            className="block text-sm font-medium text-gray-700 mb-2"
          >
            Reason for Visit
          </label>

          <textarea
            id="reason"
            value={formData.reason}
            onChange={(e) =>
              handleChange(
                "reason",
                e.target.value
              )
            }
            placeholder="Enter reason for the appointment"
            rows={4}
            className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

        </div>

      </div>

      {/* Buttons */}
      <div className="flex gap-3 mt-6">

        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg transition"
        >
          {editing
            ? "Update Appointment"
            : "Create Appointment"}
        </button>

        {editing && (
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-500 hover:bg-gray-600 text-white font-medium px-6 py-2 rounded-lg transition"
          >
            Cancel
          </button>
        )}

      </div>

    </form>
  );
}
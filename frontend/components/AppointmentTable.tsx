"use client";

import { Appointment } from "../types/appointment";

interface AppointmentTableProps {
  appointments: Appointment[];
  loading: boolean;
  onEdit: (appointment: Appointment) => void;
  onDelete: (id: number) => void;
}

export default function AppointmentTable({
  appointments,
  loading,
  onEdit,
  onDelete,
}: AppointmentTableProps) {

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">
          Appointments
        </h2>

        <p className="text-gray-600">
          Loading appointments...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">

      <h2 className="text-2xl font-bold text-gray-800 mb-6">
        Appointments
      </h2>

      {appointments.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500">
            No appointments found.
          </p>

          <p className="text-sm text-gray-400 mt-2">
            Create your first appointment using the form above.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">

          <table className="w-full border-collapse">

            <thead>
              <tr className="bg-gray-100">

                <th className="text-left px-4 py-3 border-b">
                  Patient
                </th>

                <th className="text-left px-4 py-3 border-b">
                  Doctor
                </th>

                <th className="text-left px-4 py-3 border-b">
                  Date
                </th>

                <th className="text-left px-4 py-3 border-b">
                  Time
                </th>

                <th className="text-left px-4 py-3 border-b">
                  Reason
                </th>

                <th className="text-left px-4 py-3 border-b">
                  Status
                </th>

                <th className="text-center px-4 py-3 border-b">
                  Actions
                </th>

              </tr>
            </thead>

            <tbody>

              {appointments.map((appointment) => (

                <tr
                  key={appointment.id}
                  className="hover:bg-gray-50"
                >

                  <td className="px-4 py-3 border-b">
                    {appointment.patient_name}
                  </td>

                  <td className="px-4 py-3 border-b">
                    {appointment.doctor_name}
                  </td>

                  <td className="px-4 py-3 border-b">
                    {appointment.appointment_date}
                  </td>

                  <td className="px-4 py-3 border-b">
                    {appointment.start_time}
                    {" - "}
                    {appointment.end_time}
                  </td>

                  <td className="px-4 py-3 border-b">
                    {appointment.reason || "—"}
                  </td>

                  <td className="px-4 py-3 border-b">

                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                        appointment.status === "cancelled"
                          ? "bg-red-100 text-red-700"
                          : appointment.status === "completed"
                          ? "bg-green-100 text-green-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {appointment.status}
                    </span>

                  </td>

                  <td className="px-4 py-3 border-b">

                    <div className="flex justify-center gap-2">

                      <button
                        type="button"
                        onClick={() =>
                          onEdit(appointment)
                        }
                        className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1 rounded-md text-sm"
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          onDelete(appointment.id)
                        }
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-md text-sm"
                      >
                        Cancel
                      </button>

                    </div>

                  </td>

                </tr>

              ))}

            </tbody>

          </table>

        </div>
      )}

    </div>
  );
}
"use client";

import { useEffect, useState } from "react";

import MedicationForm from "../components/MedicationForm";
import MedicationTable from "../components/MedicationTable";
import Notification from "../components/Notification";

import AppointmentForm from "../components/AppointmentForm";
import AppointmentTable from "../components/AppointmentTable";

import {
  getMedications,
  addMedication,
  updateMedication,
  deleteMedication,
} from "../services/api";

import {
  getAppointments,
  addAppointment,
  updateAppointment,
  deleteAppointment,
} from "../services/api";

import {
  Medication,
  MedicationFormData,
} from "../types/medication";

import {
  Appointment,
  AppointmentFormData,
} from "../types/appointment";


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


export default function Home() {

  // ==========================================================
  // MEDICATION STATE
  // ==========================================================

  const [formData, setFormData] =
    useState<MedicationFormData>(
      emptyMedicationForm
    );

  const [medications, setMedications] =
    useState<Medication[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [editingId, setEditingId] =
    useState<number | null>(null);


  // ==========================================================
  // APPOINTMENT STATE
  // ==========================================================

  const [
    appointmentFormData,
    setAppointmentFormData
  ] = useState<AppointmentFormData>(
    emptyAppointmentForm
  );

  const [
    appointments,
    setAppointments
  ] = useState<Appointment[]>([]);

  const [
    appointmentLoading,
    setAppointmentLoading
  ] = useState(true);

  const [
    appointmentEditingId,
    setAppointmentEditingId
  ] = useState<number | null>(null);


  // ==========================================================
  // NOTIFICATION STATE
  // ==========================================================

  const [notification, setNotification] =
    useState("");

  const [notificationType, setNotificationType] =
    useState<"success" | "error">(
      "success"
    );


  // ==========================================================
  // LOAD MEDICATIONS
  // ==========================================================

  async function loadMedications() {

    setLoading(true);

    try {

      const data = await getMedications();

      setMedications(data);

    }

    catch (error) {

      console.error(error);

      setNotificationType("error");

      setNotification(
        "Unable to load medications."
      );

    }

    finally {

      setLoading(false);

    }

  }


  // ==========================================================
  // LOAD APPOINTMENTS
  // ==========================================================

  async function loadAppointments() {

    setAppointmentLoading(true);

    try {

      const data = await getAppointments();

      setAppointments(data);

    }

    catch (error) {

      console.error(error);

      setNotificationType("error");

      setNotification(
        "Unable to load appointments."
      );

    }

    finally {

      setAppointmentLoading(false);

    }

  }


  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {

    loadMedications();

    loadAppointments();

  }, []);


  // ==========================================================
  // MEDICATION FORM
  // ==========================================================

  function clearMedicationForm() {

    setFormData(
      emptyMedicationForm
    );

    setEditingId(null);

  }


  // ==========================================================
  // APPOINTMENT FORM
  // ==========================================================

  function clearAppointmentForm() {

    setAppointmentFormData(
      emptyAppointmentForm
    );

    setAppointmentEditingId(null);

  }


  // ==========================================================
  // SUCCESS MESSAGE
  // ==========================================================

  function showSuccess(
    message: string
  ) {

    setNotificationType(
      "success"
    );

    setNotification(message);

    setTimeout(() => {

      setNotification("");

    }, 3000);

  }


  // ==========================================================
  // ERROR MESSAGE
  // ==========================================================

  function showError(
    message: string
  ) {

    setNotificationType(
      "error"
    );

    setNotification(message);

    setTimeout(() => {

      setNotification("");

    }, 3000);

  }


  // ==========================================================
  // MEDICATION SUBMIT
  // ==========================================================

  async function handleSubmit() {

    if (
      formData.medicine_name.trim() === "" ||
      formData.dosage.trim() === "" ||
      formData.frequency.trim() === "" ||
      formData.start_date === "" ||
      formData.end_date === ""
    ) {

      showError(
        "Please fill in all medication fields."
      );

      return;

    }


    if (
      formData.end_date <
      formData.start_date
    ) {

      showError(
        "End date cannot be before start date."
      );

      return;

    }


    try {

      if (
        editingId === null
      ) {

        await addMedication(
          formData
        );

        showSuccess(
          "Medication added successfully."
        );

      }

      else {

        await updateMedication(
          editingId,
          formData
        );

        showSuccess(
          "Medication updated successfully."
        );

      }


      clearMedicationForm();

      loadMedications();

    }

    catch (error) {

      console.error(error);

      showError(
        "Unable to save medication."
      );

    }

  }


  // ==========================================================
  // EDIT MEDICATION
  // ==========================================================

  function handleEdit(
    medication: Medication
  ) {

    setEditingId(
      medication.id
    );

    setFormData({

      medicine_name:
        medication.medicine_name,

      dosage:
        medication.dosage,

      frequency:
        medication.frequency,

      start_date:
        medication.start_date,

      end_date:
        medication.end_date,

    });


    window.scrollTo({

      top: 0,

      behavior: "smooth",

    });

  }


  // ==========================================================
  // DELETE MEDICATION
  // ==========================================================

  async function handleDelete(
    id: number
  ) {

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this medication?"
      );


    if (!confirmed) {

      return;

    }


    try {

      await deleteMedication(id);

      showSuccess(
        "Medication deleted successfully."
      );

      loadMedications();

    }

    catch (error) {

      console.error(error);

      showError(
        "Unable to delete medication."
      );

    }

  }


  // ==========================================================
  // CREATE / UPDATE APPOINTMENT
  // ==========================================================

  async function handleAppointmentSubmit() {

    if (
      appointmentFormData.patient_name.trim() === "" ||
      appointmentFormData.patient_email.trim() === "" ||
      appointmentFormData.doctor_name.trim() === "" ||
      appointmentFormData.appointment_date === "" ||
      appointmentFormData.start_time === "" ||
      appointmentFormData.end_time === "" ||
      appointmentFormData.reason.trim() === "" ||
      appointmentFormData.location.trim() === ""
    ) {

      showError(
        "Please fill in all appointment fields."
      );

      return;

    }


    if (
      appointmentFormData.end_time <=
      appointmentFormData.start_time
    ) {

      showError(
        "End time must be later than start time."
      );

      return;

    }


    try {

      if (
        appointmentEditingId === null
      ) {

        await addAppointment(
          appointmentFormData
        );

        showSuccess(
          "Appointment created successfully."
        );

      }

      else {

        await updateAppointment(
          appointmentEditingId,
          appointmentFormData
        );

        showSuccess(
          "Appointment updated successfully."
        );

      }


      clearAppointmentForm();

      loadAppointments();

    }

    catch (error) {

      console.error(error);

      showError(
        "Unable to save appointment."
      );

    }

  }


  // ==========================================================
  // EDIT APPOINTMENT
  // ==========================================================

  function handleAppointmentEdit(
    appointment: Appointment
  ) {

    setAppointmentEditingId(
      appointment.id
    );

    setAppointmentFormData({

      patient_name:
        appointment.patient_name,

      patient_email:
        appointment.patient_email,

      doctor_name:
        appointment.doctor_name,

      appointment_date:
        appointment.appointment_date,

      start_time:
        appointment.start_time,

      end_time:
        appointment.end_time,

      reason:
        appointment.reason,

      location:
        appointment.location,

    });


    window.scrollTo({

      top: 0,

      behavior: "smooth",

    });

  }


  // ==========================================================
  // DELETE APPOINTMENT
  // ==========================================================

  async function handleAppointmentDelete(
    id: number
  ) {

    const confirmed =
      window.confirm(
        "Are you sure you want to cancel this appointment?"
      );


    if (!confirmed) {

      return;

    }


    try {

      await deleteAppointment(id);

      showSuccess(
        "Appointment cancelled successfully."
      );

      loadAppointments();

    }

    catch (error) {

      console.error(error);

      showError(
        "Unable to cancel appointment."
      );

    }

  }


  // ==========================================================
  // PAGE
  // ==========================================================

  return (

    <main className="min-h-screen bg-slate-100">

      <div className="max-w-7xl mx-auto px-6 py-10">


        {/* PAGE HEADER */}

        <h1 className="text-4xl font-bold text-center text-blue-700 mb-2">

          HealthCare Management System

        </h1>


        <p className="text-center text-gray-600 mb-8">

          Manage medications and medical appointments.

        </p>


        {/* NOTIFICATION */}

        <Notification
          message={notification}
          type={notificationType}
        />


        {/* ==================================================
            MEDICATION SECTION
        ================================================== */}

        <section className="mb-12">

          <h2 className="text-3xl font-bold text-gray-800 mb-6">

            Medication Management

          </h2>


          <MedicationForm

            formData={formData}

            setFormData={setFormData}

            onSubmit={handleSubmit}

            editing={
              editingId !== null
            }

            onCancel={
              clearMedicationForm
            }

          />


          <MedicationTable

            medications={medications}

            loading={loading}

            onEdit={handleEdit}

            onDelete={handleDelete}

          />

        </section>


        {/* ==================================================
            APPOINTMENT SECTION
        ================================================== */}

        <section>

          <h2 className="text-3xl font-bold text-gray-800 mb-6">

            Appointment Management

          </h2>


          <AppointmentForm

            formData={
              appointmentFormData
            }

            setFormData={
              setAppointmentFormData
            }

            onSubmit={
              handleAppointmentSubmit
            }

            editing={
              appointmentEditingId !== null
            }

            onCancel={
              clearAppointmentForm
            }

          />


          <AppointmentTable

            appointments={
              appointments
            }

            loading={
              appointmentLoading
            }

            onEdit={
              handleAppointmentEdit
            }

            onDelete={
              handleAppointmentDelete
            }

          />

        </section>


      </div>

    </main>

  );

}
"use client";

import { useEffect, useState } from "react";

import MedicationForm from "../components/MedicationForm";
import MedicationTable from "../components/MedicationTable";
import Notification from "../components/Notification";

import {
  getMedications,
  addMedication,
  updateMedication,
  deleteMedication,
} from "../services/api";

import {
  Medication,
  MedicationFormData,
} from "../types/medication";

const emptyForm: MedicationFormData = {
  medicine_name: "",
  dosage: "",
  frequency: "",
  start_date: "",
  end_date: "",
};

export default function Home() {

  const [formData, setFormData] =
    useState<MedicationFormData>(emptyForm);

  const [medications, setMedications] =
    useState<Medication[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [editingId, setEditingId] =
    useState<number | null>(null);

  const [notification, setNotification] =
    useState("");

  const [notificationType, setNotificationType] =
    useState<"success" | "error">("success");



  async function loadMedications() {

    setLoading(true);

    try {

      const data = await getMedications();

      setMedications(data);

    }

    catch (error) {

      console.error(error);

      setNotificationType("error");

      setNotification("Unable to load medications.");

    }

    finally {

      setLoading(false);

    }

  }



  useEffect(() => {

    loadMedications();

  }, []);




  function clearForm() {

    setFormData(emptyForm);

    setEditingId(null);

  }




  function showSuccess(message: string) {

    setNotificationType("success");

    setNotification(message);

    setTimeout(() => {

      setNotification("");

    }, 3000);

  }




  function showError(message: string) {

    setNotificationType("error");

    setNotification(message);

    setTimeout(() => {

      setNotification("");

    }, 3000);

  }




  async function handleSubmit() {

    if (
      formData.medicine_name.trim() === "" ||
      formData.dosage.trim() === "" ||
      formData.frequency.trim() === "" ||
      formData.start_date === "" ||
      formData.end_date === ""
    ) {

      showError("Please fill in all fields.");

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

      if (editingId === null) {

        await addMedication(formData);

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

      clearForm();

      loadMedications();

    }

    catch (error) {

      console.error(error);

      showError(
        "Unable to save medication."
      );

    }

  }  function handleEdit(
    medication: Medication
  ) {

    setEditingId(medication.id);

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




  async function handleDelete(
    id: number
  ) {

    const confirmed = window.confirm(

      "Are you sure you want to delete this medication?"

    );

    if (!confirmed) return;

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




  return (

    <main className="min-h-screen bg-slate-100">

      <div className="max-w-7xl mx-auto px-6 py-10">

        <h1 className="text-4xl font-bold text-center text-blue-700 mb-2">

          Medication Management System

        </h1>

        <p className="text-center text-gray-600 mb-8">

          Manage prescriptions and medications for patients.

        </p>

        <Notification

          message={notification}

          type={notificationType}

        />

        <MedicationForm

          formData={formData}

          setFormData={setFormData}

          onSubmit={handleSubmit}

          editing={editingId !== null}

          onCancel={clearForm}

        />

        <MedicationTable

          medications={medications}

          loading={loading}

          onEdit={handleEdit}

          onDelete={handleDelete}

        />

      </div>

    </main>

  );}


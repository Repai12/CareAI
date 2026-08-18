import axios from "axios";

import {
  Medication,
  MedicationFormData,
} from "../types/medication";

import {
  Appointment,
  AppointmentFormData,
} from "../types/appointment";

import {
  VisitNote,
  VisitNoteCreate,
  VisitNoteUpdate,
} from "../types/visitNote";


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";


function authHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("careai_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}


// ============================================================
// MEDICATION API
// ============================================================

const MEDICATION_API =
  `${API_BASE_URL}/medications`;


export const getMedications = async (
  patientId: string
): Promise<Medication[]> => {

  const response = await axios.get(
    `${MEDICATION_API}/patient/${patientId}`,
    { headers: authHeaders() }
  );

  return response.data;
};


export const addMedication = async (
  patientId: string,
  data: MedicationFormData
): Promise<Medication> => {

  const response = await axios.post(
    `${MEDICATION_API}/`,
    { ...data, patient_id: patientId },
    { headers: authHeaders() }
  );

  return response.data;
};


export const updateMedication = async (
  id: string,
  data: MedicationFormData
): Promise<Medication> => {

  const response = await axios.put(
    `${MEDICATION_API}/${id}`,
    data,
    { headers: authHeaders() }
  );

  return response.data;
};


export const deleteMedication = async (
  id: string
): Promise<void> => {

  await axios.delete(
    `${MEDICATION_API}/${id}`,
    { headers: authHeaders() }
  );
};


// ============================================================
// APPOINTMENT API
// ============================================================

const APPOINTMENT_API =
  `${API_BASE_URL}/appointments`;


export const getAppointments = async (
  patientId: string
): Promise<Appointment[]> => {

  const response = await axios.get(
    `${APPOINTMENT_API}/patient/${patientId}`,
    { headers: authHeaders() }
  );

  return response.data;
};


export const addAppointment = async (
  data: AppointmentFormData
): Promise<Appointment> => {

  const response = await axios.post(
    `${APPOINTMENT_API}/`,
    data,
    { headers: authHeaders() }
  );

  return response.data;
};


export const updateAppointment = async (
  id: string,
  data: AppointmentFormData
): Promise<Appointment> => {

  const response = await axios.put(
    `${APPOINTMENT_API}/${id}`,
    data,
    { headers: authHeaders() }
  );

  return response.data;
};


export const deleteAppointment = async (
  id: string
): Promise<void> => {

  await axios.delete(
    `${APPOINTMENT_API}/${id}`,
    { headers: authHeaders() }
  );
};


// ============================================================
// VISIT NOTES API
// ============================================================

const VISIT_NOTE_API =
  `${API_BASE_URL}/visit-notes`;


export const getVisitNotes = async (
  patientName?: string
): Promise<VisitNote[]> => {

  const response = await axios.get(
    `${VISIT_NOTE_API}/`,
    {
      params: patientName ? { patient_name: patientName } : {},
      headers: authHeaders(),
    }
  );

  return response.data;
};


export const addVisitNote = async (
  data: VisitNoteCreate
): Promise<VisitNote> => {

  const response = await axios.post(
    `${VISIT_NOTE_API}/`,
    data,
    { headers: authHeaders() }
  );

  return response.data;
};


export const updateVisitNote = async (
  id: number,
  data: VisitNoteUpdate
): Promise<VisitNote> => {

  const response = await axios.put(
    `${VISIT_NOTE_API}/${id}`,
    data,
    { headers: authHeaders() }
  );

  return response.data;
};

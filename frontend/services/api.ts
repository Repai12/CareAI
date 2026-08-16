import axios from "axios";

import {
  Medication,
  MedicationFormData,
} from "../types/medication";

import {
  Appointment,
  AppointmentFormData,
} from "../types/appointment";


const API_BASE_URL =
  "http://127.0.0.1:8000";


// ============================================================
// MEDICATION API
// ============================================================

const MEDICATION_API =
  `${API_BASE_URL}/medications`;


export const getMedications = async (): Promise<
  Medication[]
> => {

  const response = await axios.get(
    `${MEDICATION_API}/`
  );

  return response.data;
};


export const addMedication = async (
  data: MedicationFormData
): Promise<Medication> => {

  const response = await axios.post(
    `${MEDICATION_API}/`,
    data
  );

  return response.data;
};


export const updateMedication = async (
  id: string,
  data: MedicationFormData
): Promise<Medication> => {

  const response = await axios.put(
    `${MEDICATION_API}/${id}`,
    data
  );

  return response.data;
};


export const deleteMedication = async (
  id: string
): Promise<void> => {

  await axios.delete(
    `${MEDICATION_API}/${id}`
  );
};


// ============================================================
// APPOINTMENT API
// ============================================================

const APPOINTMENT_API =
  `${API_BASE_URL}/appointments`;


export const getAppointments = async (): Promise<
  Appointment[]
> => {

  const response = await axios.get(
    `${APPOINTMENT_API}/`
  );

  return response.data;
};


export const addAppointment = async (
  data: AppointmentFormData
): Promise<Appointment> => {

  const response = await axios.post(
    `${APPOINTMENT_API}/`,
    data
  );

  return response.data;
};


export const updateAppointment = async (
  id: string,
  data: AppointmentFormData
): Promise<Appointment> => {

  const response = await axios.put(
    `${APPOINTMENT_API}/${id}`,
    data
  );

  return response.data;
};


export const deleteAppointment = async (
  id: string
): Promise<void> => {

  await axios.delete(
    `${APPOINTMENT_API}/${id}`
  );
};
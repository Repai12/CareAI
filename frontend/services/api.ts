import axios from "axios";

import { MedicationFormData } from "../types/medication";
import {
  Appointment,
  AppointmentFormData,
} from "../types/appointment";


// ============================================================
// MEDICATION API
// ============================================================

const MEDICATION_API =
  "http://127.0.0.1:8000/medications";


export const getMedications = async () => {

  const response = await axios.get(
    `${MEDICATION_API}/`
  );

  return response.data;

};


export const addMedication = async (
  data: MedicationFormData
) => {

  const response = await axios.post(
    `${MEDICATION_API}/`,
    data
  );

  return response.data;

};


export const updateMedication = async (
  id: number,
  data: MedicationFormData
) => {

  const response = await axios.put(
    `${MEDICATION_API}/${id}`,
    data
  );

  return response.data;

};


export const deleteMedication = async (
  id: number
) => {

  const response = await axios.delete(
    `${MEDICATION_API}/${id}`
  );

  return response.data;

};


// ============================================================
// APPOINTMENT API
// ============================================================

const APPOINTMENT_API =
  "http://127.0.0.1:8000/appointments";


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
) => {

  const response = await axios.post(
    `${APPOINTMENT_API}/`,
    data
  );

  return response.data;

};


export const updateAppointment = async (
  id: number,
  data: AppointmentFormData
) => {

  const response = await axios.put(
    `${APPOINTMENT_API}/${id}`,
    data
  );

  return response.data;

};


export const deleteAppointment = async (
  id: number
) => {

  const response = await axios.delete(
    `${APPOINTMENT_API}/${id}`
  );

  return response.data;

};
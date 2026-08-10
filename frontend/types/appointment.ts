export interface Appointment {
  id: number;

  patient_name: string;
  patient_email: string;

  doctor_name: string;

  appointment_date: string;
  start_time: string;
  end_time: string;

  reason: string;
  location: string;

  status: string;
  google_event_id: string | null;
}


export interface AppointmentFormData {
  patient_name: string;
  patient_email: string;

  doctor_name: string;

  appointment_date: string;
  start_time: string;
  end_time: string;

  reason: string;
  location: string;
}
export interface VisitNote {
  id: number;
  patient_name: string;
  doctor_name: string;
  appointment_id: string | null;
  visit_date: string;
  notes: string;
  prescription: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface VisitNoteCreate {
  patient_name: string;
  doctor_name: string;
  appointment_id?: string | null;
  visit_date: string;
  notes: string;
  prescription?: string | null;
}

export interface VisitNoteUpdate {
  notes?: string | null;
  prescription?: string | null;
}
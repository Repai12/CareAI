export interface Medication {
  id: string;
  medicine_name: string;
  dosage: string;
  frequency: string;
  start_date: string | null;
  end_date: string | null;
}

export interface MedicationFormData {
  medicine_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date: string;
}
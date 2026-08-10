export interface Medication {
  id: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date: string;
}

export interface MedicationFormData {
  medicine_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date: string;
}
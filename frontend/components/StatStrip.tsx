import { VitalsOut, MedicationOut, AppointmentOut } from "@/lib/api";

export default function StatStrip({
  vitals,
  medications,
  appointments,
  reportsSentThisWeek,
}: {
  vitals: VitalsOut | null;
  medications: MedicationOut[];
  appointments: AppointmentOut[];
  reportsSentThisWeek: number;
}) {
  const nextAppt = appointments[0];

  const stats = [
    {
      label: "Latest BP",
      value: vitals ? vitals.blood_pressure : "—",
      accent: "text-steel",
    },
    {
      label: "Active meds",
      value: String(medications.length),
      accent: "text-sage",
    },
    {
      label: "Next appointment",
      value: nextAppt ? new Date(nextAppt.scheduled_at).toLocaleDateString() : "None",
      accent: "text-gold",
    },
    {
      label: "Reports sent this week",
      value: String(reportsSentThisWeek),
      accent: "text-ink/60",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {stats.map((s) => (
        <div key={s.label} className="bg-white rounded-xl border border-sageLight px-4 py-3">
          <p className="text-xs text-ink/40 uppercase tracking-wide font-medium mb-1">{s.label}</p>
          <p className={`text-lg font-display font-semibold ${s.accent}`}>{s.value}</p>
        </div>
      ))}
    </div>
  );
}

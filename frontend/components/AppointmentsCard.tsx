import SectionCard from "./SectionCard";
import { AppointmentOut } from "@/lib/api";

export default function AppointmentsCard({ appointments }: { appointments: AppointmentOut[] }) {
  return (
    <SectionCard eyebrow={`${appointments.length} upcoming`} title="Appointments">
      {appointments.length === 0 ? (
        <p className="text-ink/50 text-sm">No upcoming appointments.</p>
      ) : (
        <ul className="space-y-3">
          {appointments.map((a) => (
            <li key={a.id} className="flex items-center justify-between border-l-4 border-gold pl-3">
              <div>
                <p className="font-medium text-ink">{a.doctor_name}</p>
                <p className="text-sm text-ink/50">{a.location || "Location TBD"}</p>
              </div>
              <p className="text-sm text-ink/60">
                {new Date(a.scheduled_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

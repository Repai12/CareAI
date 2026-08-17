import SectionCard from "./SectionCard";
import { HeartPulseIcon } from "./icons";
import { VitalsOut } from "@/lib/api";

export default function VitalsCard({ vitals }: { vitals: VitalsOut | null }) {
  return (
    <SectionCard eyebrow="Latest reading" title="Vitals" icon={<HeartPulseIcon />} accent="steel">
      {!vitals ? (
        <p className="text-ink/50 text-sm">No vitals logged yet.</p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <Stat label="Blood pressure" value={vitals.blood_pressure} />
          <Stat label="Sugar level" value={`${vitals.sugar_level} mg/dL`} />
          <Stat label="Heart rate" value={`${vitals.heart_rate} bpm`} />
          <Stat label="Temperature" value={`${vitals.temperature} °C`} />
          <p className="col-span-2 text-xs text-ink/40 mt-1">
            Recorded {new Date(vitals.logged_at).toLocaleString()}
          </p>
        </div>
      )}
    </SectionCard>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-steel/5 rounded-lg px-4 py-3">
      <p className="text-xs text-steel font-medium">{label}</p>
      <p className="text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}

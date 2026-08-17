import SectionCard from "./SectionCard";
import { PillIcon } from "./icons";
import { MedicationOut } from "@/lib/api";

export default function MedicationsCard({ medications }: { medications: MedicationOut[] }) {
  return (
    <SectionCard
      eyebrow={`${medications.length} active`}
      title="Medications"
      icon={<PillIcon />}
      accent="sage"
    >
      {medications.length === 0 ? (
        <p className="text-ink/50 text-sm">No active medications.</p>
      ) : (
        <ul className="divide-y divide-sageLight">
          {medications.map((m) => (
            <li key={m.id} className="py-3 flex items-center justify-between">
              <div>
                <p className="font-medium text-ink">{m.name}</p>
                <p className="text-sm text-ink/50">{m.dosage} · {m.frequency}</p>
              </div>
              <span className="text-xs text-sage bg-sageLight rounded-full px-3 py-1">
                {m.schedule_time}
              </span>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

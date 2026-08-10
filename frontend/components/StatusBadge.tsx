import { VitalsOut } from "@/lib/api";

/**
 * A single at-a-glance "how is this patient doing" signal, derived from
 * the most recent vitals reading. Simple, transparent thresholds - not a
 * medical diagnosis, just a visual anchor for the dashboard header.
 */
export default function StatusBadge({ vitals }: { vitals: VitalsOut | null }) {
  if (!vitals) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full bg-ink/5 text-ink/50">
        No data yet
      </span>
    );
  }

  const [systolic] = vitals.blood_pressure.split("/").map(Number);
  const needsAttention = systolic >= 140 || vitals.heart_rate >= 100 || vitals.sugar_level >= 180;

  if (needsAttention) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full bg-alert/10 text-alert">
        <span className="w-1.5 h-1.5 rounded-full bg-alert" />
        Needs attention
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full bg-sageLight text-sage">
      <span className="w-1.5 h-1.5 rounded-full bg-sage" />
      Stable
    </span>
  );
}

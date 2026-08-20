import Link from "next/link";
import { ClipboardIcon, DocumentSearchIcon, StethoscopeIcon, LeafIcon, SmileIcon, ActivityIcon } from "./icons";
import LogoutButton from "@/components/LogoutButton";

const TABS = [
  { segment: "", label: "Overview", icon: null },
  { segment: "vitals", label: "Vitals", icon: ClipboardIcon },
  { segment: "reports", label: "AI Reports", icon: DocumentSearchIcon },
  { segment: "symptoms", label: "Symptom Checker", icon: StethoscopeIcon },
  { segment: "diet", label: "Diet Advisor", icon: LeafIcon },
  { segment: "mood", label: "Mood", icon: SmileIcon },
  { segment: "activity", label: "Activity", icon: ActivityIcon },
];

export default function HealthNav({ patientId, current }: { patientId: string; current: string }) {
  return (
    <nav className="flex flex-wrap items-center gap-2 mb-6 border-b border-sageLight pb-4">
      <Link
        href={`/dashboard/${patientId}`}
        className="text-xs font-medium text-ink/50 hover:text-sage border border-sageLight rounded-full px-3 py-1.5 transition mr-2"
      >
        ← Dashboard
      </Link>
      {TABS.map((tab) => {
        const href = tab.segment ? `/health/${patientId}/${tab.segment}` : `/health/${patientId}`;
        const isActive = current === tab.segment;
        return (
          <Link
            key={tab.segment || "overview"}
            href={href}
            className={`flex items-center gap-1.5 text-xs font-medium rounded-full px-3 py-1.5 transition ${
              isActive ? "bg-sage text-white" : "text-sage border border-sageLight hover:bg-sageLight"
            }`}
          >
            {tab.icon && <tab.icon className="w-3.5 h-3.5" />}
            {tab.label}
          </Link>
        );
      })}
      <div className="ml-auto">
        <LogoutButton />
      </div>
    </nav>
  );
}

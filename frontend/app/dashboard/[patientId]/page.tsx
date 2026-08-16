"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { DashboardResponse, WeeklyReportOut, getDashboard, getReportHistory } from "@/lib/api";
import VitalsCard from "@/components/VitalsCard";
import MedicationsCard from "@/components/MedicationsCard";
import AppointmentsCard from "@/components/AppointmentsCard";
import ReportPanel from "@/components/ReportPanel";
import StatStrip from "@/components/StatStrip";
import StatusBadge from "@/components/StatusBadge";
import AISummaryPanel from "@/components/AISummaryPanel";

function initials(name: string) {
  return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function DashboardPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [data, setData] = useState<DashboardResponse | null>(null);
  const [reportHistory, setReportHistory] = useState<WeeklyReportOut[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;

    Promise.all([getDashboard(patientId), getReportHistory(patientId)])
      .then(([dashboard, history]) => {
        setData(dashboard);
        setReportHistory(history);
      })
      .catch((e) => setError(e.message));
  }, [patientId]);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-alert">{error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-ink/50">Loading dashboard...</p>
      </main>
    );
  }

  const reportsSentThisWeek = reportHistory.filter((r) => {
    const sentAt = new Date(r.sent_at);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return sentAt >= weekAgo;
  }).length;

  const roleLabel = role === "patient" ? "Your Dashboard" : role === "doctor" ? "Viewing as Doctor" : role === "family" ? "Viewing as Family" : "";

  return (
    <main className="min-h-screen px-6 py-10 max-w-5xl mx-auto">
      <header className="mb-8 flex items-start justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-sage text-white flex items-center justify-center text-lg font-display font-semibold shrink-0">
            {initials(data.patient.name)}
          </div>
          <div>
            <p className="text-sm text-sage font-medium">CareAI · {roleLabel}</p>
            <h1 className="text-3xl font-display font-bold text-ink mt-0.5">{data.patient.name}</h1>
            <p className="text-ink/50 text-sm">{data.patient.email}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Member 1 (Mubasshira) - one-line link into the Health Module */}
          <Link
            href={`/health/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Health Module
          </Link>
          <Link
            href={`/notifications/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Notifications
          </Link>
          <StatusBadge vitals={data.latest_vitals} />
        </div>
      </header>

      <StatStrip
        vitals={data.latest_vitals}
        medications={data.active_medications}
        appointments={data.upcoming_appointments}
        reportsSentThisWeek={reportsSentThisWeek}
      />

      <div className="grid md:grid-cols-2 gap-6">
        <VitalsCard vitals={data.latest_vitals} />
        <MedicationsCard medications={data.active_medications} />
        <AppointmentsCard appointments={data.upcoming_appointments} />
        <ReportPanel patientId={patientId} initialHistory={reportHistory} />
        {role === "doctor" && <AISummaryPanel patientId={patientId} />}
      </div>
    </main>
  );
}

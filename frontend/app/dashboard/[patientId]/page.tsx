"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { DashboardResponse, WeeklyReportOut, getDashboard, getReportHistory } from "@/lib/api";
import VitalsCard from "@/components/VitalsCard";
import MedicationsCard from "@/components/MedicationsCard";
import AppointmentsCard from "@/components/AppointmentsCard";
import ReportPanel from "@/components/ReportPanel";

export default function DashboardPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [data, setData] = useState<DashboardResponse | null>(null);
  const [reportHistory, setReportHistory] = useState<WeeklyReportOut[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
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

  return (
    <main className="min-h-screen px-6 py-10 max-w-5xl mx-auto">
      <header className="mb-8">
        <p className="text-sm text-sage font-medium">CareAI · Health Overview</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-1">
          {data.patient.name}
        </h1>
        <p className="text-ink/50 text-sm">{data.patient.email}</p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <VitalsCard vitals={data.latest_vitals} />
        <MedicationsCard medications={data.active_medications} />
        <AppointmentsCard appointments={data.upcoming_appointments} />
        <ReportPanel patientId={patientId} initialHistory={reportHistory} />
      </div>
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { DashboardResponse, WeeklyReportOut, getDashboard, getReportHistory, apiFetch } from "@/lib/api";
import VitalsCard from "@/components/VitalsCard";
import MedicationsCard from "@/components/MedicationsCard";
import AppointmentsCard from "@/components/AppointmentsCard";
import ReportPanel from "@/components/ReportPanel";
import StatStrip from "@/components/StatStrip";
import StatusBadge from "@/components/StatusBadge";
import AISummaryPanel from "@/components/AISummaryPanel";
import LogoutButton from "@/components/LogoutButton";

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
  const [sosLoading, setSosLoading] = useState(false);
  const [sosMessage, setSosMessage] = useState<string | null>(null);

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

  async function handleSOS() {
    if (!confirm("Are you sure you want to trigger an Emergency SOS Alert?")) return;
    setSosLoading(true);
    setSosMessage(null);
    try {
      const res = await apiFetch("/api/emergency/sos", { method: "POST" });
      setSosMessage(`SOS Alert sent: ${res.message || "processed"}`);
    } catch (e: any) {
      setSosMessage(`SOS failed: ${e.message || "could not trigger alert"}`);
    } finally {
      setSosLoading(false);
    }
  }

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
          <Link
            href={`/health/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Health Module
          </Link>
          <Link
            href={`/medications/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Medications &amp; Appointments
          </Link>
          <Link
            href={`/visit-notes/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Visit Notes
          </Link>
          <Link
            href={`/notifications/${patientId}`}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Notifications
          </Link>
          <Link
            href="/connections"
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-3 py-1.5 hover:bg-sageLight transition"
          >
            Connections
          </Link>
          <StatusBadge vitals={data.latest_vitals} />
          <LogoutButton />
        </div>
      </header>

      {sosMessage && (
        <div className="mb-6 p-3 bg-alert/10 border border-alert/30 text-alert rounded-lg text-sm font-medium">
          {sosMessage}
        </div>
      )}

      {role === "patient" && (
        <div className="mb-6">
          <button
            onClick={handleSOS}
            disabled={sosLoading}
            className="bg-alert text-white font-bold py-3 px-6 rounded-xl shadow-sm hover:opacity-90 disabled:opacity-50 transition"
          >
            {sosLoading ? "Sending..." : "🚨 Trigger Emergency SOS"}
          </button>
        </div>
      )}

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

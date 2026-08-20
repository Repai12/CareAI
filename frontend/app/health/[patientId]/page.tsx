"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getVitalsHistory, getHealthReports, getSymptomLogs, getLatestDietPlan } from "@/lib/api/vitals";
import { getMoodHistory } from "@/lib/api/mood";
import { getActivityHistory } from "@/lib/api/activity";
import { getLatestWellness } from "@/lib/api/wellness";
import HealthNav from "../_components/HealthNav";
import { ClipboardIcon, DocumentSearchIcon, StethoscopeIcon, LeafIcon, SmileIcon, ActivityIcon, SparkleIcon } from "../_components/icons";

function getMyRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("careai_role");
}

export default function HealthOverviewPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [role, setRole] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<{
    vitalsCount: number;
    latestVitals: string | null;
    reportsCount: number;
    symptomsCount: number;
    lastUrgency: string | null;
    hasDietPlan: boolean;
    adherenceRate: number | null;
    moodCount: number;
    latestMood: string | null;
    activityCount: number;
    activityMinutesThisWeek: number;
    hasWellnessTips: boolean;
  } | null>(null);

  useEffect(() => {
    setRole(getMyRole());
    if (!patientId) return;

    Promise.all([
      getVitalsHistory(patientId),
      getHealthReports(patientId),
      getSymptomLogs(patientId),
      getLatestDietPlan(patientId),
      getMoodHistory(patientId),
      getActivityHistory(patientId),
      getLatestWellness(patientId),
    ])
      .then(([vitals, reports, symptoms, diet, moods, activity, wellness]) => {
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        setSummary({
          vitalsCount: vitals.length,
          latestVitals: vitals[0] ? `BP ${vitals[0].blood_pressure} · Sugar ${vitals[0].sugar_level}` : null,
          reportsCount: reports.length,
          symptomsCount: symptoms.length,
          lastUrgency: symptoms[0]?.urgency ?? null,
          hasDietPlan: !!diet.plan,
          adherenceRate: diet.adherence_rate,
          moodCount: moods.length,
          latestMood: moods[0]?.mood ?? null,
          activityCount: activity.length,
          activityMinutesThisWeek: activity
            .filter((a) => new Date(a.logged_at).getTime() >= weekAgo)
            .reduce((sum, a) => sum + a.duration_minutes, 0),
          hasWellnessTips: !!wellness,
        });
        setLoaded(true);
      })
      .catch((e) => {
        setError(e.message);
        setLoaded(true);
      });
  }, [patientId]);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-alert">{error}</p>
      </main>
    );
  }

  if (!loaded || !summary) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-ink/50">Loading health module...</p>
      </main>
    );
  }

  const cards = [
    {
      href: `/health/${patientId}/vitals`,
      icon: ClipboardIcon,
      accent: "text-steel bg-steel/10",
      eyebrow: "Feature 1 · CRUD",
      title: "Vitals Logging",
      detail: summary.vitalsCount > 0 ? `${summary.vitalsCount} readings logged · latest: ${summary.latestVitals}` : "No vitals logged yet",
    },
    {
      href: `/health/${patientId}/reports`,
      icon: DocumentSearchIcon,
      accent: "text-gold bg-gold/15",
      eyebrow: "Feature 2 · Groq API LIVE",
      title: "AI Health Report Analyzer",
      detail: summary.reportsCount > 0 ? `${summary.reportsCount} report(s) analyzed` : "No reports uploaded yet",
    },
    {
      href: `/health/${patientId}/symptoms`,
      icon: StethoscopeIcon,
      accent: "text-alert bg-alert/10",
      eyebrow: "Feature 3 · Groq, vitals-aware + auto-escalation",
      title: "AI Symptom Checker",
      detail: summary.symptomsCount > 0 ? `${summary.symptomsCount} check(s) · last urgency: ${summary.lastUrgency}` : "No symptom checks yet",
    },
    {
      href: `/health/${patientId}/diet`,
      icon: LeafIcon,
      accent: "text-sage bg-sageLight",
      eyebrow: "Feature 4 · Groq, trend-aware + adherence tracking",
      title: "AI Diet Advisor",
      detail: summary.hasDietPlan
        ? `Plan active${summary.adherenceRate !== null ? ` · ${summary.adherenceRate}% adherence` : ""}`
        : "No diet plan yet",
    },
    {
      href: `/health/${patientId}/mood`,
      icon: SmileIcon,
      accent: "text-gold bg-gold/15",
      eyebrow: "Module 1 · Mood Tracking",
      title: "Mood Tracking",
      detail: summary.moodCount > 0
        ? `${summary.moodCount} ${summary.moodCount === 1 ? "entry" : "entries"} logged · latest: ${summary.latestMood}`
        : "No mood logged yet",
    },
    {
      href: `/health/${patientId}/activity`,
      icon: ActivityIcon,
      accent: "text-steel bg-steel/10",
      eyebrow: "Module 1 · Activity Tracking",
      title: "Activity Tracking",
      detail: summary.activityCount > 0
        ? `${summary.activityMinutesThisWeek} min this week · ${summary.activityCount} total entries`
        : "No activity logged yet",
    },
    {
      href: `/health/${patientId}/wellness`,
      icon: SparkleIcon,
      accent: "text-gold bg-gold/15",
      eyebrow: "Module 2 · Wellness Recommendation Engine",
      title: "Wellness Tips",
      detail: summary.hasWellnessTips ? "Recommendations available" : "No wellness tips generated yet",
    },
  ];

  return (
    <main className="min-h-screen px-6 py-10 max-w-5xl mx-auto">
      <header className="mb-2">
        <p className="text-sm text-sage font-medium">CareAI · Health Module (Member 1)</p>
        <h1 className="text-3xl font-display font-bold text-ink mt-0.5">Vitals, AI Reports, Symptoms &amp; Diet</h1>
      </header>

      <HealthNav patientId={patientId} current="" />

      <div className="grid md:grid-cols-2 gap-4">
        {cards.map((c) => (
          <Link
            key={c.href}
            href={c.href}
            className="bg-white rounded-xl border border-sageLight shadow-sm p-6 hover:border-sage transition block"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${c.accent}`}>
                <c.icon className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide font-semibold text-ink/40">{c.eyebrow}</p>
                <h2 className="text-lg font-display font-semibold text-ink">{c.title}</h2>
              </div>
            </div>
            <p className="text-sm text-ink/60">{c.detail}</p>
            <p className="text-xs text-sage font-medium mt-3">Open →</p>
          </Link>
        ))}
      </div>
    </main>
  );
}

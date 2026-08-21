"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyPatients, getDashboard, getNotifications, type MyPatient, type DashboardResponse } from "@/lib/api";
import { getMyRole } from "@/lib/apiClient";
import StatusBadge from "@/components/StatusBadge";
import LogoutButton from "@/components/LogoutButton";

interface PatientRow {
  patient: MyPatient;
  dashboard: DashboardResponse | null;
  unreadCount: number;
  hasUnreadEmergency: boolean;
}

function initials(name: string) {
  return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

/**
 * README S2: /family/dashboard ("list of linked patients + latest status
 * per patient") and /doctor/dashboard ("list of assigned patients,
 * flagged/urgent first"). Previously this page just listed names - no
 * status, no sorting, nothing to actually act on without clicking into
 * every single patient one by one.
 */
export default function PatientsListPage() {
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);
  const [rows, setRows] = useState<PatientRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const r = getMyRole();
    setRole(r);

    if (r === "patient") {
      // A patient only ever has one dashboard - themselves. Resolve and
      // send them straight there instead of showing a list of one.
      getMyPatients()
        .then((mine) => {
          if (mine[0]) router.replace(`/dashboard/${mine[0].id}`);
        })
        .catch((e) => setError(e.message));
      return;
    }

    getMyPatients()
      .then(async (list) => {
        if (list.length === 1) {
          router.replace(`/dashboard/${list[0].id}`);
          return;
        }

        const withStatus = await Promise.all(
          list.map(async (patient): Promise<PatientRow> => {
            const [dashboard, notifPage] = await Promise.all([
              getDashboard(patient.id).catch(() => null),
              getNotifications(patient.id).catch(() => ({ items: [], next_cursor: null })),
            ]);
            const unread = notifPage.items.filter((n) => !n.is_read);
            return {
              patient,
              dashboard,
              unreadCount: unread.length,
              hasUnreadEmergency: unread.some((n) => n.category === "EMERGENCY"),
            };
          })
        );

        // Doctors see flagged/urgent patients first (README S2); family
        // just gets unread-first, which is the natural equivalent.
        withStatus.sort((a, b) => {
          if (a.hasUnreadEmergency !== b.hasUnreadEmergency) return a.hasUnreadEmergency ? -1 : 1;
          return b.unreadCount - a.unreadCount;
        });

        setRows(withStatus);
      })
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-alert">{error}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-sage font-medium">CareAI</p>
          <h1 className="text-2xl font-display font-bold text-ink mt-0.5">
            {role === "doctor" ? "Your patients" : "Your linked patients"}
          </h1>
          {role === "doctor" && <p className="text-ink/50 text-sm mt-1">Flagged/urgent patients are shown first.</p>}
        </div>
        <LogoutButton />
      </header>

      {!rows && <p className="text-ink/50 text-sm">Loading...</p>}

      {rows && rows.length === 0 && (
        <p className="text-ink/50 text-sm">
          No patients linked to your account yet.{" "}
          <Link href="/connections" className="text-sage font-medium">
            Check your connections
          </Link>{" "}
          or ask a patient for their code to get started.
        </p>
      )}

      {rows && rows.length > 0 && (
        <ul className="space-y-2">
          {rows.map(({ patient, dashboard, unreadCount, hasUnreadEmergency }) => (
            <li key={patient.id}>
              <Link
                href={`/dashboard/${patient.id}`}
                className={`flex items-center gap-4 bg-white border rounded-xl p-4 hover:border-sage transition ${
                  hasUnreadEmergency ? "border-alert/40" : "border-sageLight"
                }`}
              >
                <div className="w-11 h-11 rounded-full bg-sage text-white flex items-center justify-center text-sm font-display font-semibold shrink-0">
                  {initials(patient.name)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-ink text-sm">{patient.name}</p>
                  <p className="text-xs text-ink/50">
                    {dashboard?.upcoming_appointments?.[0]
                      ? `Next appointment ${dashboard.upcoming_appointments[0].appointment_date}`
                      : "No upcoming appointments"}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {unreadCount > 0 && (
                    <span
                      className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                        hasUnreadEmergency ? "bg-alert text-white" : "bg-gold/15 text-gold"
                      }`}
                    >
                      {unreadCount} unread
                    </span>
                  )}
                  <StatusBadge vitals={dashboard?.latest_vitals ?? null} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

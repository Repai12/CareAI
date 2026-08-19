"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getMyPatients } from "@/lib/api";
import { getMyRole } from "@/lib/apiClient";

interface PatientSummary {
  id: string;
  name: string;
  email: string;
  role: string;
}

function initials(name: string) {
  return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
}

/**
 * The list a family member or doctor lands on when linked to more than
 * one patient (README S2: /family/dashboard, /doctor/dashboard - "List
 * of linked/assigned patients"). Previously there was no such page at
 * all: login always redirected straight to patients[0], so anyone
 * linked to a second patient had no way to ever see or reach it.
 */
export default function PatientsListPage() {
  const router = useRouter();
  const [patients, setPatients] = useState<PatientSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const role = getMyRole();
    if (role === "patient") {
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
      .then((list) => {
        if (list.length === 1) {
          router.replace(`/dashboard/${list[0].id}`);
          return;
        }
        setPatients(list);
      })
      .catch((e) => setError(e.message));
  }, [router]);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-paper">
        <p className="text-alert">{error}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-10 max-w-2xl mx-auto">
      <header className="mb-6">
        <p className="text-sm text-sage font-medium">CareAI</p>
        <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Your patients</h1>
      </header>

      {!patients && <p className="text-ink/50 text-sm">Loading...</p>}

      {patients && patients.length === 0 && (
        <p className="text-ink/50 text-sm">
          No patients linked to your account yet.{" "}
          <Link href="/connections" className="text-sage font-medium">
            Check your connections
          </Link>{" "}
          or ask a patient for their code to get started.
        </p>
      )}

      {patients && patients.length > 0 && (
        <ul className="space-y-2">
          {patients.map((p) => (
            <li key={p.id}>
              <Link
                href={`/dashboard/${p.id}`}
                className="flex items-center gap-4 bg-white border border-sageLight rounded-xl p-4 hover:border-sage transition"
              >
                <div className="w-11 h-11 rounded-full bg-sage text-white flex items-center justify-center text-sm font-display font-semibold shrink-0">
                  {initials(p.name)}
                </div>
                <div>
                  <p className="font-medium text-ink text-sm">{p.name}</p>
                  <p className="text-xs text-ink/50">{p.email}</p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

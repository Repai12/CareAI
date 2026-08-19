"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  getMyConnections,
  approveConnection,
  declineConnection,
  revokeConnection,
  updateConnectionPermission,
  getMyPatients,
  type CareLink,
} from "@/lib/api/me";
import { getMyRole } from "@/lib/apiClient";

const STATUS_STYLES: Record<string, string> = {
  pending: "border-gold bg-gold/10 text-gold",
  active: "border-sage bg-sageLight text-sage",
  declined: "border-ink/20 bg-ink/5 text-ink/50",
  revoked: "border-ink/20 bg-ink/5 text-ink/50",
};

export default function ConnectionsPage() {
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);
  const [links, setLinks] = useState<CareLink[]>([]);
  const [myCode, setMyCode] = useState<string | null>(null);
  const [codeCopied, setCodeCopied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingOn, setActingOn] = useState<string | null>(null);

  function load() {
    setLoading(true);
    getMyConnections()
      .then(setLinks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const r = getMyRole();
    setRole(r);
    load();
    // The code is only ever shown once, at registration - if it's lost,
    // there was previously no way to look it up again to share with a
    // new family member/doctor. getMyPatients() for a patient returns
    // [self], which carries their own patient_code.
    if (r === "patient") {
      getMyPatients()
        .then((mine) => setMyCode(mine[0]?.patient_code ?? null))
        .catch(() => {});
    }
  }, []);

  function copyCode() {
    if (!myCode) return;
    navigator.clipboard.writeText(myCode).then(() => {
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 2000);
    });
  }

  async function act(linkId: string, action: () => Promise<CareLink>) {
    setActingOn(linkId);
    try {
      const updated = await action();
      setLinks((prev) => prev.map((l) => (l.id === updated.id ? updated : l)));
    } catch (e: any) {
      setError(e.message || "That action failed.");
    } finally {
      setActingOn(null);
    }
  }

  const isPatient = role === "patient";
  const pending = links.filter((l) => l.status === "pending");
  const active = links.filter((l) => l.status === "active");
  const other = links.filter((l) => l.status === "declined" || l.status === "revoked");

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <header className="mb-6">
        <p className="text-sm text-sage font-medium">CareAI · Connections</p>
        <h1 className="text-2xl font-display font-bold text-ink mt-0.5">
          {isPatient ? "Family & doctor access" : "Your connections"}
        </h1>
        <p className="text-ink/50 text-sm mt-1">
          {isPatient
            ? "Approve or revoke who can see your health data. Nothing is shared until you approve it here."
            : "Patients you've asked to connect with, and whether they've approved it yet."}
        </p>
      </header>

      {isPatient && myCode && (
        <div className="mb-8 bg-white border border-sageLight rounded-xl p-4 flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs uppercase tracking-wide text-ink/40 font-semibold mb-1">Your patient code</p>
            <p className="text-2xl font-display font-bold text-sage tracking-wide">{myCode}</p>
            <p className="text-xs text-ink/50 mt-1">
              Share this with family or your doctor - they enter it when they register to request a connection.
            </p>
          </div>
          <button
            onClick={copyCode}
            className="text-xs font-medium text-sage border border-sageLight rounded-full px-4 py-2 hover:bg-sageLight transition shrink-0"
          >
            {codeCopied ? "Copied!" : "Copy code"}
          </button>
        </div>
      )}

      {error && <p className="text-alert text-sm mb-4">{error}</p>}
      {loading && <p className="text-ink/50 text-sm">Loading...</p>}

      {!loading && links.length === 0 && (
        <p className="text-ink/50 text-sm">
          {isPatient
            ? "No one has requested access yet. Share your patient code with family or your doctor so they can register and connect."
            : "You haven't connected to a patient yet. Register or ask the patient for their code to connect."}
        </p>
      )}

      {isPatient && pending.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-ink/70 mb-3">Pending requests</h2>
          <ul className="space-y-3">
            {pending.map((l) => (
              <li key={l.id} className="bg-white border border-gold/40 rounded-xl p-4">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <p className="font-medium text-ink text-sm">
                      {l.viewer_name} <span className="text-ink/50 font-normal">wants to connect as your {l.link_role}</span>
                    </p>
                    <p className="text-xs text-ink/40 mt-1">Requested {new Date(l.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button
                      onClick={() => act(l.id, () => approveConnection(l.id))}
                      disabled={actingOn === l.id}
                      className="text-xs font-medium bg-sage text-white px-3 py-1.5 rounded-lg hover:bg-sage/90 disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => act(l.id, () => declineConnection(l.id))}
                      disabled={actingOn === l.id}
                      className="text-xs font-medium text-alert border border-alert/30 px-3 py-1.5 rounded-lg hover:bg-alert/10 disabled:opacity-50"
                    >
                      Decline
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {active.length > 0 && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold text-ink/70 mb-3">Active</h2>
          <ul className="space-y-3">
            {active.map((l) => (
              <li key={l.id} className="bg-white border border-sageLight rounded-xl p-4">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <p className="font-medium text-ink text-sm">
                      {isPatient ? l.viewer_name : l.patient_name}
                      <span className="text-ink/50 font-normal"> · {l.link_role}</span>
                    </p>
                    <p className="text-xs text-ink/40 mt-1">
                      {l.permission_level === "view_and_manage" ? "Can view and manage" : "View only"}
                      {l.responded_at && ` · connected ${new Date(l.responded_at).toLocaleDateString()}`}
                    </p>
                  </div>
                  {isPatient && (
                    <div className="flex gap-2 shrink-0 items-center">
                      <button
                        onClick={() =>
                          act(l.id, () =>
                            updateConnectionPermission(
                              l.id,
                              l.permission_level === "view_only" ? "view_and_manage" : "view_only"
                            )
                          )
                        }
                        disabled={actingOn === l.id}
                        className="text-xs font-medium text-sage border border-sageLight px-3 py-1.5 rounded-lg hover:bg-sageLight disabled:opacity-50"
                      >
                        {l.permission_level === "view_only" ? "Allow managing" : "Make view-only"}
                      </button>
                      <button
                        onClick={() => act(l.id, () => revokeConnection(l.id))}
                        disabled={actingOn === l.id}
                        className="text-xs font-medium text-alert border border-alert/30 px-3 py-1.5 rounded-lg hover:bg-alert/10 disabled:opacity-50"
                      >
                        Revoke
                      </button>
                    </div>
                  )}
                  {!isPatient && (
                    <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${STATUS_STYLES.active}`}>
                      Active
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {other.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold text-ink/70 mb-3">Past</h2>
          <ul className="space-y-2">
            {other.map((l) => (
              <li key={l.id} className="bg-white border border-sageLight rounded-xl p-4 opacity-60">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <p className="text-sm text-ink">
                    {isPatient ? l.viewer_name : l.patient_name} <span className="text-ink/50">· {l.link_role}</span>
                  </p>
                  <span className={`text-xs font-medium px-2.5 py-1 rounded-full border capitalize ${STATUS_STYLES[l.status]}`}>
                    {l.status}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <button onClick={() => router.back()} className="inline-block mt-8 text-sm text-sage font-medium hover:underline">
        Back
      </button>
    </main>
  );
}

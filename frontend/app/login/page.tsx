"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, getMyPatients, resendVerification } from "@/lib/api";

type DemoRole = "patient" | "doctor" | "family";

// Matches backend/seed_demo_data.py - update both together.
const DEMO_ACCOUNTS: Record<DemoRole, { email: string; label: string }> = {
  patient: { email: "patient@demo.com", label: "Patient" },
  doctor: { email: "doctor@demo.com", label: "Doctor" },
  family: { email: "family@demo.com", label: "Family / Well-wisher" },
};

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState<DemoRole>("doctor");
  const [email, setEmail] = useState(DEMO_ACCOUNTS.doctor.email);
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resendStatus, setResendStatus] = useState<"idle" | "sending" | "sent">("idle");

  function handleRoleSelect(r: DemoRole) {
    setRole(r);
    setEmail(DEMO_ACCOUNTS[r].email);
  }

  async function handleResend() {
    setResendStatus("sending");
    try {
      await resendVerification(email);
    } finally {
      setResendStatus("sent");
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResendStatus("idle");
    setLoading(true);
    try {
      await login(email, password);

      const patients = await getMyPatients();
      if (patients.length === 0) {
        setError("Signed in, but no patient is linked to this account yet.");
        setLoading(false);
        return;
      }
      // Exactly one patient -> straight to their dashboard. More than one
      // (a family member or doctor linked to multiple patients) -> the
      // list page, since there's no single "right" one to guess.
      if (patients.length === 1) {
        router.push(`/dashboard/${patients[0].id}`);
      } else {
        router.push("/patients");
      }
    } catch (err: any) {
      setError(err.message || "Login failed");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm">
        <h1 className="text-2xl font-display font-semibold text-ink mb-1">CareAI</h1>
        <p className="text-ink/50 text-sm mb-6">Sign in to your health dashboard</p>

        <label className="block text-sm text-ink/70 mb-2">I am signing in as</label>
        <div className="grid grid-cols-3 gap-2 mb-5">
          {(Object.keys(DEMO_ACCOUNTS) as DemoRole[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => handleRoleSelect(r)}
              className={`text-xs font-medium py-2 rounded-lg border transition ${
                role === r ? "bg-sage text-white border-sage" : "bg-white text-ink/60 border-sageLight hover:border-sage"
              }`}
            >
              {DEMO_ACCOUNTS[r].label}
            </button>
          ))}
        </div>

        <label className="block text-sm text-ink/70 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm text-ink/70">Password</label>
          <Link href="/forgot-password" className="text-xs text-sage font-medium">
            Forgot password?
          </Link>
        </div>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        {error && (
          <div className="mb-3">
            <p className="text-alert text-sm">{error}</p>
            {error.toLowerCase().includes("verify your email") && (
              <div className="mt-1.5">
                {resendStatus === "sent" ? (
                  <p className="text-xs text-sage">If that email is registered and not yet verified, a new link has been sent.</p>
                ) : (
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={resendStatus === "sending"}
                    className="text-xs text-sage font-medium hover:underline disabled:opacity-50"
                  >
                    {resendStatus === "sending" ? "Sending..." : "Resend verification email"}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-sm text-ink/50 text-center mt-4">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-sage font-medium">
            Sign up
          </Link>
        </p>
      </form>
    </main>
  );
}

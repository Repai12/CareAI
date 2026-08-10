"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, getMyPatients } from "@/lib/api";

type Role = "patient" | "family" | "doctor";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("patient");
  const [patientEmail, setPatientEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          name,
          email,
          password,
          role,
          patient_email: role !== "patient" ? patientEmail : undefined,
        }),
      });

      const loginRes = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("careai_token", loginRes.access_token);

      const patients = await getMyPatients();
      if (patients.length === 0) {
        router.push("/login");
        return;
      }
      router.push(`/dashboard/${patients[0].id}`);
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper py-10">
      <form
        onSubmit={handleSubmit}
        className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm"
      >
        <h1 className="text-2xl font-display font-semibold text-ink mb-1">Create account</h1>
        <p className="text-ink/50 text-sm mb-6">Join CareAI</p>

        <label className="block text-sm text-ink/70 mb-1">Full name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        <label className="block text-sm text-ink/70 mb-1">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        <label className="block text-sm text-ink/70 mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        <label className="block text-sm text-ink/70 mb-2">I am a</label>
        <div className="grid grid-cols-3 gap-2 mb-4">
          {(["patient", "family", "doctor"] as Role[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`text-xs font-medium py-2 rounded-lg border capitalize transition ${
                role === r
                  ? "bg-sage text-white border-sage"
                  : "bg-white text-ink/60 border-sageLight hover:border-sage"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {role !== "patient" && (
          <>
            <label className="block text-sm text-ink/70 mb-1">
              Patient&apos;s email (whose records you&apos;ll view)
            </label>
            <input
              type="email"
              value={patientEmail}
              onChange={(e) => setPatientEmail(e.target.value)}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              placeholder="patient@example.com"
              required
            />
            <p className="text-xs text-ink/40 -mt-3 mb-4">
              The patient must already have a CareAI account with this email.
            </p>
          </>
        )}

        {error && <p className="text-alert text-sm mb-3">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
        >
          {loading ? "Creating account..." : "Create account"}
        </button>

        <p className="text-sm text-ink/50 text-center mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-sage font-medium">
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}

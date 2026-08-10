"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, getMyPatients } from "@/lib/api";

type DemoRole = "patient" | "doctor" | "family";

const DEMO_ACCOUNTS: Record<DemoRole, { email: string; label: string }> = {
  patient: { email: "patient@demo.com", label: "Patient" },
  doctor: { email: "repai1001+doctor@gmail.com", label: "Doctor" },
  family: { email: "repai1001+family@gmail.com", label: "Family / Well-wisher" },
};

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState<DemoRole>("doctor");
  const [email, setEmail] = useState(DEMO_ACCOUNTS.doctor.email);
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function handleRoleSelect(r: DemoRole) {
    setRole(r);
    setEmail(DEMO_ACCOUNTS[r].email);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await login(email, password);
      localStorage.setItem("careai_token", res.access_token);

      const patients = await getMyPatients();
      if (patients.length === 0) {
        setError("Signed in, but no patient is linked to this account yet.");
        setLoading(false);
        return;
      }
      router.push(`/dashboard/${patients[0].id}`);
    } catch (err: any) {
      setError(err.message || "Login failed");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper">
      <form
        onSubmit={handleSubmit}
        className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm"
      >
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
                role === r
                  ? "bg-sage text-white border-sage"
                  : "bg-white text-ink/60 border-sageLight hover:border-sage"
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

        <label className="block text-sm text-ink/70 mb-1">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
          required
        />

        {error && <p className="text-alert text-sm mb-3">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}
"use client";

import { useState } from "react";
import Link from "next/link";
import { register, type RegisterResponse } from "@/lib/api";
import AuthBackdrop from "@/components/AuthBackdrop";

type Role = "patient" | "family" | "doctor";

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("patient");
  const [patientCode, setPatientCode] = useState("");
  const [licenseNumber, setLicenseNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RegisterResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const registerRes = await register({
        name,
        email,
        password,
        role,
        patient_code: role !== "patient" ? patientCode : undefined,
        license_number: role === "doctor" ? licenseNumber : undefined,
      });
      // Accounts require email verification before they can log in - no
      // auto-login here, since /auth/login would just reject it (S3.1).
      setResult(registerRes);
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <AuthBackdrop>
        <div className="bg-white/95 backdrop-blur-sm border border-sageLight rounded-xl shadow-lg p-8 w-full max-w-sm text-center">
          <h1 className="text-2xl font-display font-semibold text-ink mb-2">Check your email</h1>
          <p className="text-ink/60 text-sm mb-4">
            We sent a verification link to <span className="font-medium">{email}</span>. Click it to activate your
            account, then sign in.
          </p>
          {result.patient_code && (
            <>
              <p className="text-ink/60 text-sm mb-2">
                Once verified, share this code with family members or your doctor so they can link to your account:
              </p>
              <p className="text-2xl font-display font-bold text-sage tracking-wide mb-4">{result.patient_code}</p>
            </>
          )}
          {result.doctor_unverified_notice && (
            <p className="text-xs text-ink/50 bg-paper border border-sageLight rounded-lg p-3 mb-4">
              {result.doctor_unverified_notice}
            </p>
          )}
          <Link href="/login" className="text-sage font-medium text-sm">
            Go to sign in
          </Link>
        </div>
      </AuthBackdrop>
    );
  }

  return (
    <AuthBackdrop>
      <form
        onSubmit={handleSubmit}
        className="bg-white/95 backdrop-blur-sm border border-sageLight rounded-xl shadow-lg p-8 w-full max-w-sm"
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

        {role === "patient" ? (
          <p className="text-xs text-ink/40 mb-4">
            You&apos;ll get a unique Patient Code after signing up - share it with family or your doctor so they can link to your account.
          </p>
        ) : (
          <>
            <label className="block text-sm text-ink/70 mb-1">Patient&apos;s code</label>
            <input
              value={patientCode}
              onChange={(e) => setPatientCode(e.target.value.toUpperCase())}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              placeholder="CARE-1234"
              required
            />
            <p className="text-xs text-ink/40 -mt-3 mb-4">
              Ask the patient for their code - they get it when they register.
            </p>
          </>
        )}

        {role === "doctor" && (
          <>
            <label className="block text-sm text-ink/70 mb-1">Medical license / registration number</label>
            <input
              value={licenseNumber}
              onChange={(e) => setLicenseNumber(e.target.value)}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              required
            />
            <p className="text-xs text-ink/40 -mt-3 mb-4">
              Not checked against a real registry in this version - your account is marked unverified until an admin
              reviews it.
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
    </AuthBackdrop>
  );
}

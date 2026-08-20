"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { resetPassword } from "@/lib/api";

export default function ResetPasswordPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    setLoading(true);
    try {
      await resetPassword(params.token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 2500);
    } catch (err: any) {
      setError(err.message || "Couldn't reset your password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm">
        <h1 className="text-2xl font-display font-semibold text-ink mb-1">Set a new password</h1>

        {done ? (
          <p className="text-ink/70 text-sm mt-4">Password updated. Taking you to sign in...</p>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6">
            <label className="block text-sm text-ink/70 mb-1">New password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              required
            />
            <label className="block text-sm text-ink/70 mb-1">Confirm new password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              required
            />
            {error && <p className="text-alert text-sm mb-3">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
            >
              {loading ? "Saving..." : "Reset password"}
            </button>
          </form>
        )}

        <p className="text-sm text-ink/50 text-center mt-4">
          <Link href="/login" className="text-sage font-medium">
            Back to sign in
          </Link>
        </p>
      </div>
    </main>
  );
}

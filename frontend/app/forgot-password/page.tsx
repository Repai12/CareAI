"use client";

import { useState } from "react";
import Link from "next/link";
import { forgotPassword } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      // Backend always returns the same generic message whether or not
      // the email exists (README S3.3), so there's nothing to branch on
      // here beyond "the request completed."
      await forgotPassword(email);
    } finally {
      setSent(true);
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper">
      <div className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm">
        <h1 className="text-2xl font-display font-semibold text-ink mb-1">Reset your password</h1>
        <p className="text-ink/50 text-sm mb-6">
          Enter your account email and we&apos;ll send you a reset link.
        </p>

        {sent ? (
          <p className="text-ink/70 text-sm">
            If that email is registered, a reset link has been sent. Check your inbox.
          </p>
        ) : (
          <form onSubmit={handleSubmit}>
            <label className="block text-sm text-ink/70 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-sageLight rounded-lg px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-sage"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
            >
              {loading ? "Sending..." : "Send reset link"}
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

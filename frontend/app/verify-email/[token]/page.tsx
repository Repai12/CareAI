"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail, resendVerification } from "@/lib/api";
import AuthBackdrop from "@/components/AuthBackdrop";

export default function VerifyEmailPage() {
  const params = useParams<{ token: string }>();
  const [status, setStatus] = useState<"checking" | "success" | "error">("checking");
  const [message, setMessage] = useState("");
  const [resendEmail, setResendEmail] = useState("");
  const [resendStatus, setResendStatus] = useState<"idle" | "sending" | "sent">("idle");
  const hasCalledRef = useRef(false);

  useEffect(() => {
    // Guards against React Strict Mode's dev-only double-invoke of mount
    // effects. Unlike an idempotent GET, this token is single-use server-
    // side - a second call for the same token always fails with "already
    // used" even though the first one just succeeded, so a plain
    // cancellation-flag guard isn't enough here (both calls fire before
    // either resolves); the ref has to stop the second call from ever
    // going out.
    if (hasCalledRef.current) return;
    hasCalledRef.current = true;

    verifyEmail(params.token)
      .then((res) => {
        setStatus("success");
        setMessage(res.message);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err.message || "This verification link is invalid.");
      });
  }, [params.token]);

  async function handleResend(e: React.FormEvent) {
    e.preventDefault();
    if (!resendEmail.trim()) return;
    setResendStatus("sending");
    try {
      await resendVerification(resendEmail.trim());
    } finally {
      setResendStatus("sent");
    }
  }

  return (
    <AuthBackdrop>
      <div className="bg-white/95 backdrop-blur-sm border border-sageLight rounded-xl shadow-lg p-8 w-full max-w-sm text-center">
        {status === "checking" && (
          <>
            <h1 className="text-2xl font-display font-semibold text-ink mb-2">Verifying...</h1>
            <p className="text-ink/60 text-sm">One moment.</p>
          </>
        )}
        {status === "success" && (
          <>
            <h1 className="text-2xl font-display font-semibold text-ink mb-2">Email verified</h1>
            <p className="text-ink/60 text-sm mb-4">{message}</p>
            <Link href="/login" className="text-sage font-medium text-sm">
              Go to sign in
            </Link>
          </>
        )}
        {status === "error" && (
          <>
            <h1 className="text-2xl font-display font-semibold text-ink mb-2">Verification failed</h1>
            <p className="text-alert text-sm mb-4">{message}</p>

            {resendStatus === "sent" ? (
              <p className="text-sage text-sm mb-4">If that email is registered and not yet verified, a new link has been sent.</p>
            ) : (
              <form onSubmit={handleResend} className="mb-4 flex gap-2">
                <input
                  type="email"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  placeholder="Your email"
                  className="flex-1 border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage"
                  required
                />
                <button
                  type="submit"
                  disabled={resendStatus === "sending"}
                  className="text-xs font-medium bg-sage text-white px-3 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition shrink-0"
                >
                  {resendStatus === "sending" ? "..." : "Get new link"}
                </button>
              </form>
            )}

            <Link href="/register" className="text-sage font-medium text-sm">
              Back to sign up
            </Link>
          </>
        )}
      </div>
    </AuthBackdrop>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/lib/api";

export default function VerifyEmailPage() {
  const params = useParams<{ token: string }>();
  const [status, setStatus] = useState<"checking" | "success" | "error">("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
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

  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm text-center">
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
            <Link href="/register" className="text-sage font-medium text-sm">
              Back to sign up
            </Link>
          </>
        )}
      </div>
    </main>
  );
}

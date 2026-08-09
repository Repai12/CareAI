"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await login(email, password);
      localStorage.setItem("careai_token", res.access_token);
      router.push("/"); // send them onward once you have a real landing/redirect
    } catch (err: any) {
      setError(err.message || "Login failed");
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper">
      <form
        onSubmit={handleSubmit}
        className="bg-white border border-sageLight rounded-xl shadow-sm p-8 w-full max-w-sm"
      >
        <h1 className="text-2xl font-display font-semibold text-ink mb-1">CareAI</h1>
        <p className="text-ink/50 text-sm mb-6">Sign in (temporary stub - team auth pending)</p>

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
          className="w-full bg-sage text-white font-medium py-2 rounded-lg hover:bg-sage/90 transition"
        >
          Sign in
        </button>
      </form>
    </main>
  );
}

import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-4 bg-paper">
      <h1 className="text-3xl font-display font-bold text-ink">CareAI</h1>
      <p className="text-ink/50">AI-Powered Elderly Health Monitoring Platform</p>
      <Link
        href="/login"
        className="bg-sage text-white font-medium px-5 py-2 rounded-lg hover:bg-sage/90 transition"
      >
        Sign in
      </Link>
    </main>
  );
}

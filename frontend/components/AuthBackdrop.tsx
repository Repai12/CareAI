/**
 * Warm, photo-backed wrapper for the sign-in/sign-up flow (login, register,
 * forgot/reset password, verify email) - the one place a full-strength
 * photo is appropriate, since there's no dashboard data to compete with
 * yet. The scrim keeps the card's own contrast untouched; it only darkens
 * the photo itself.
 */
export default function AuthBackdrop({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10 relative overflow-hidden bg-ink">
      <div
        aria-hidden
        className="absolute inset-0 bg-cover bg-center scale-105"
        style={{ backgroundImage: "url(/images/care-hero.jpg)" }}
      />
      <div aria-hidden className="absolute inset-0 bg-gradient-to-t from-ink/85 via-ink/45 to-sage/40" />
      <div className="relative z-10 w-full flex justify-center">{children}</div>
    </main>
  );
}

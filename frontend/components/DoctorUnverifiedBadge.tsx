/**
 * DoctorUnverifiedBadge.tsx
 * ----------------------------
 * README S13 "known gap": doctor accounts require a license/registration
 * number at signup, but it's never checked against a real registry -
 * every doctor account is unverified in that sense, permanently, not
 * just until they confirm their email. Previously this was only ever
 * shown once, on the registration success screen - this makes it
 * persistent wherever a doctor's identity is shown to a patient/family
 * viewer, so the disclosure isn't easy to miss or forget.
 */
export default function DoctorUnverifiedBadge() {
  return (
    <span
      title="Doctor accounts on CareAI are not checked against a real medical license registry in this version."
      className="inline-flex items-center gap-1 text-[10px] font-medium text-gold bg-gold/10 border border-gold/30 rounded-full px-2 py-0.5 align-middle cursor-help"
    >
      ⚠ Unverified license
    </span>
  );
}

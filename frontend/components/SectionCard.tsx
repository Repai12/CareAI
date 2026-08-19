type Accent = "sage" | "steel" | "gold" | "alert";

const ACCENT_STYLES: Record<Accent, { bg: string; text: string }> = {
  sage: { bg: "bg-sageLight", text: "text-sage" },
  steel: { bg: "bg-steel/10", text: "text-steel" },
  gold: { bg: "bg-gold/15", text: "text-gold" },
  alert: { bg: "bg-alert/10", text: "text-alert" },
};

export default function SectionCard({
  title,
  eyebrow,
  icon,
  accent = "sage",
  disclaimer,
  children,
}: {
  title: string;
  eyebrow: string;
  icon?: React.ReactNode;
  accent?: Accent;
  /** Optional fine-print shown under the title - use for "AI-generated, not a diagnosis" on AI-output panels (README S7.1/S8.1/S8.2). */
  disclaimer?: string;
  children: React.ReactNode;
}) {
  const style = ACCENT_STYLES[accent];
  return (
    <div className="bg-white rounded-xl border border-sageLight shadow-sm p-6">
      <div className="flex items-center gap-3 mb-4">
        {icon && (
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${style.bg} ${style.text}`}>
            {icon}
          </div>
        )}
        <div>
          <p className={`text-xs uppercase tracking-wide font-semibold ${style.text}`}>
            {eyebrow}
          </p>
          <h2 className="text-xl font-display font-semibold text-ink">{title}</h2>
        </div>
      </div>
      {disclaimer && <p className="text-xs text-ink/40 italic mb-4 -mt-2">{disclaimer}</p>}
      {children}
    </div>
  );
}

export default function SectionCard({
  title,
  eyebrow,
  children,
}: {
  title: string;
  eyebrow: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-sageLight shadow-sm p-6">
      <p className="text-xs uppercase tracking-wide text-sage font-semibold mb-1">
        {eyebrow}
      </p>
      <h2 className="text-xl font-display font-semibold text-ink mb-4">
        {title}
      </h2>
      {children}
    </div>
  );
}

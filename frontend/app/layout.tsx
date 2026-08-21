import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareAI",
  description: "AI-Powered Elderly Health Monitoring Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body">
        {/* Soft, blurred color shapes behind every page - fixed so they
            never scroll or repeat per-page, and pointer-events-none/aria-
            hidden so they're purely decorative and never intercept a
            click or get read out to a screen reader. Kept low-opacity so
            they never compete with foreground text/card contrast - the
            goal is "feels like a considered care platform," not "busy." */}
        <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
          {/* Faint, grayscale echo of the sign-in photo - a quiet reminder
              of who this app is for, kept low-opacity so it never competes
              with foreground text/card contrast. */}
          <div
            className="absolute inset-0 bg-cover bg-center opacity-[0.05] grayscale"
            style={{ backgroundImage: "url(/images/care-hero.jpg)" }}
          />
          <div className="absolute -top-40 -right-32 w-[36rem] h-[36rem] rounded-full bg-sage/[0.07] blur-3xl" />
          <div className="absolute top-1/3 -left-48 w-[32rem] h-[32rem] rounded-full bg-gold/[0.08] blur-3xl" />
          <div className="absolute bottom-[-12rem] right-1/4 w-[30rem] h-[30rem] rounded-full bg-steel/[0.06] blur-3xl" />
        </div>
        {children}
      </body>
    </html>
  );
}

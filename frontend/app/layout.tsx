import "./globals.css";

export const metadata: Metadata = {
  title: "CareAI",
  description: "AI-Powered Elderly Health Monitoring Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body">{children}</body>
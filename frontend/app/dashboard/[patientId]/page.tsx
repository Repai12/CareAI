"use client";

import { useState } from "react";
import { StatStrip } from "@/components/StatStrip";
import { VitalsCard } from "@/components/VitalsCard";
import { MedicationsCard } from "@/components/MedicationsCard";
import { AppointmentsCard } from "@/components/AppointmentsCard";
import { AISummaryPanel } from "@/components/AISummaryPanel";

export default function PatientDashboard({ params }: { params: { patientId: string } }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  // Trigger SOS Alert via Twilio
  const handleSOS = async () => {
    if (!confirm("Are you sure you want to trigger an Emergency SOS Alert?")) return;
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/emergency/sos", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        setMessage("🚨 SOS Alert successfully sent to emergency contacts!");
      } else {
        setMessage(`❌ SOS Failed: ${data.detail || "Error triggering alert"}`);
      }
    } catch (err) {
      setMessage("❌ Failed to connect to server for SOS Alert.");
    } finally {
      setLoading(false);
    }
  };

  // Trigger Daily Safety Check-in
  const handleCheckin = async () => {
    setLoading(true);
    setMessage(null);
    try {
      const res = await fetch("/api/emergency/checkin", { method: "POST" });
      if (res.ok) {
        setMessage("✅ Daily Safety Check-in completed successfully!");
      } else {
        setMessage("❌ Check-in failed. Please try again.");
      }
    } catch (err) {
      setMessage("❌ Network error while sending check-in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner Message */}
      {message && (
        <div className="p-4 bg-blue-50 border border-blue-200 text-blue-800 rounded-lg text-center font-medium shadow-sm">
          {message}
        </div>
      )}

      {/* Member-3 Emergency & Safety Control Panel */}
      <div className="bg-white p-6 rounded-xl border border-red-100 shadow-sm space-y-4">
        <h2 className="text-xl font-bold text-gray-800 border-b pb-2">
          🚨 Emergency & Safety Actions (Member-3 Features)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* One-Tap SOS Button */}
          <button
            onClick={handleSOS}
            disabled={loading}
            className="w-full bg-red-600 hover:bg-red-700 active:scale-95 text-white font-extrabold py-4 px-6 rounded-xl shadow-md transition-all text-lg flex items-center justify-center gap-2"
          >
            🚨 TRIGGER SOS ALERT
          </button>

          {/* Daily Safety Check-in Button */}
          <button
            onClick={handleCheckin}
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold py-4 px-6 rounded-xl shadow-md transition-all text-lg flex items-center justify-center gap-2"
          >
            ✅ DAILY SAFETY CHECK-IN
          </button>
        </div>
      </div>

      {/* Standard Dashboard Components */}
      <StatStrip patientId={params.patientId} />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <VitalsCard patientId={params.patientId} />
        <MedicationsCard patientId={params.patientId} />
        <AppointmentsCard patientId={params.patientId} />
      </div>

      <AISummaryPanel patientId={params.patientId} />
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { triggerSOS } from "@/lib/api/emergency";

type Phase = "idle" | "countdown" | "sending";

const COUNTDOWN_SECONDS = 3;

/**
 * Replaces the old native `confirm()` dialog with an on-page countdown -
 * same pattern real safety apps use (a brief, cancellable delay catches
 * an accidental tap without adding real friction to a genuine
 * emergency, unlike a modal dialog that adds a click either way).
 * Cancelling never sends a request at all.
 */
export default function SOSButton() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [secondsLeft, setSecondsLeft] = useState(COUNTDOWN_SECONDS);
  const [message, setMessage] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  function startCountdown() {
    setMessage(null);
    setSecondsLeft(COUNTDOWN_SECONDS);
    setPhase("countdown");
    timerRef.current = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          fireSOS();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }

  function cancelCountdown() {
    if (timerRef.current) clearInterval(timerRef.current);
    setPhase("idle");
  }

  async function fireSOS() {
    setPhase("sending");
    try {
      const res = await triggerSOS();
      if (res.already_sent) {
        setMessage(res.message);
      } else if (res.failed_to.length > 0) {
        setMessage(`SOS sent. Delivered to ${res.delivered_to.length}, failed to reach ${res.failed_to.length} contact(s).`);
      } else if (res.delivered_to.length === 0) {
        setMessage("SOS logged and family/doctor notified - no emergency contacts on file to text. Add one in Safety.");
      } else {
        setMessage(`SOS sent to all ${res.delivered_to.length} emergency contact(s).`);
      }
    } catch (e: any) {
      setMessage(`SOS failed: ${e.message || "could not trigger alert"}`);
    } finally {
      setPhase("idle");
    }
  }

  return (
    <div className="mb-6">
      {message && (
        <div className="mb-3 p-3 bg-alert/10 border border-alert/30 text-alert rounded-lg text-sm font-medium">
          {message}
        </div>
      )}

      {phase === "countdown" ? (
        <div
          className="flex items-center gap-3 bg-alert/10 border border-alert/30 rounded-xl p-3"
          role="alert"
          aria-live="assertive"
        >
          <span className="text-alert font-bold text-lg">Sending SOS in {secondsLeft}...</span>
          <button
            onClick={cancelCountdown}
            className="bg-white text-alert font-bold py-2 px-4 rounded-lg border border-alert/40 hover:bg-alert/5 transition"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button
          onClick={startCountdown}
          disabled={phase === "sending"}
          className="bg-alert text-white font-bold py-3 px-6 rounded-xl shadow-sm hover:opacity-90 disabled:opacity-50 transition"
        >
          {phase === "sending" ? "Sending..." : "🚨 Trigger Emergency SOS"}
        </button>
      )}
    </div>
  );
}

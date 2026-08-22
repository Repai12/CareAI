"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getNotifications, markNotificationsRead, NotificationOut } from "@/lib/api/notifications";
import LogoutButton from "@/components/LogoutButton";

const CATEGORIES = [
  { value: "", label: "All" },
  { value: "EMERGENCY", label: "Emergency" },
  { value: "MEDICATION", label: "Medication" },
  { value: "APPOINTMENT", label: "Appointments" },
  { value: "SAFETY", label: "Safety" },
  { value: "CONNECTION", label: "Connections" },
  { value: "DIGEST", label: "Daily Digest" },
];

const CATEGORY_COLORS: Record<string, string> = {
  EMERGENCY: "border-alert bg-alert/5",
  MEDICATION: "border-sage bg-sageLight",
  APPOINTMENT: "border-gold bg-gold/10",
  SAFETY: "border-steel bg-steel/5",
  CONNECTION: "border-steel/60 bg-steel/10",
  DIGEST: "border-sage/50 bg-sageLight/50",
};

export default function NotificationsPage() {
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [items, setItems] = useState<NotificationOut[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load(reset: boolean) {
    setLoading(true);
    getNotifications(patientId, category || undefined, reset ? undefined : nextCursor || undefined)
      .then((page) => {
        setItems(reset ? page.items : [...items, ...page.items]);
        setNextCursor(page.next_cursor);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId, category]);

  async function handleMarkAllRead() {
    await markNotificationsRead(patientId);
    setItems(items.map((i) => ({ ...i, is_read: true })));
  }

  const unreadCount = items.filter((i) => !i.is_read).length;

  return (
    <main className="min-h-screen px-6 py-10 max-w-3xl mx-auto">
      <nav className="flex flex-wrap items-center gap-2 mb-6">
        <Link
          href={`/dashboard/${patientId}`}
          className="text-xs font-medium text-ink/50 hover:text-sage border border-sageLight rounded-full px-3 py-1.5 transition"
        >
          ← Dashboard
        </Link>
        <div className="ml-auto">
          <LogoutButton />
        </div>
      </nav>

      <header className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <div>
          <p className="text-sm text-sage font-medium">CareAI · Family Notification Center</p>
          <h1 className="text-2xl font-display font-bold text-ink mt-0.5">
            Events {unreadCount > 0 && <span className="text-alert text-base font-normal">· {unreadCount} unread</span>}
          </h1>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="text-sm bg-sage text-white px-4 py-2 rounded-lg hover:bg-sage/90"
          >
            Mark all as read
          </button>
        )}
      </header>

      <div className="flex gap-2 mb-6 flex-wrap">
        {CATEGORIES.map((c) => (
          <button
            key={c.value}
            onClick={() => setCategory(c.value)}
            className={`text-xs font-medium px-3 py-1.5 rounded-full border transition ${
              category === c.value
                ? "bg-sage text-white border-sage"
                : "bg-white text-ink/60 border-sageLight hover:border-sage"
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {error && <p className="text-alert text-sm">{error}</p>}

      {items.length === 0 && !loading ? (
        <p className="text-ink/50 text-sm">No events yet.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((n) => (
            <li
              key={n.id}
              className={`border-l-4 rounded-lg p-4 bg-white border border-sageLight ${
                CATEGORY_COLORS[n.category] || "border-ink/20"
              } ${n.is_read ? "opacity-60" : ""}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-ink text-sm">{n.title}</p>
                  <p className="text-ink/60 text-sm mt-0.5">{n.message}</p>
                </div>
                {!n.is_read && (
                  <span className="w-2 h-2 rounded-full bg-alert shrink-0 mt-1.5" />
                )}
              </div>
              <p className="text-xs text-ink/40 mt-2">{new Date(n.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>
      )}

      {nextCursor && (
        <button
          onClick={() => load(false)}
          disabled={loading}
          className="mt-4 text-sm text-sage font-medium hover:underline disabled:opacity-50"
        >
          {loading ? "Loading..." : "Load more"}
        </button>
      )}
    </main>
  );
}

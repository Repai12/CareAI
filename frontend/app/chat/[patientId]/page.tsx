"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getChatHistory, getChatWebSocketUrl, type ChatMessageOut } from "@/lib/api/chat";
import { getToken, getMyUserId } from "@/lib/apiClient";

type ConnectionStatus = "connecting" | "open" | "reconnecting" | "denied" | "closed";

export default function ChatPage() {
  const params = useParams<{ patientId: string }>();
  const router = useRouter();
  const patientId = params.patientId;

  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [draft, setDraft] = useState("");
  const myUserId = getMyUserId();
  const bottomRef = useRef<HTMLDivElement>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptedRef = useRef(false);

  function openSocket() {
    // Guards against React Strict Mode's dev-only double-invoke of mount
    // effects (and any other accidental double-call): without this, two
    // live sockets can end up registered for one tab, and every incoming
    // broadcast then gets appended twice.
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    const token = getToken();
    if (!token) {
      setStatus("denied");
      return;
    }
    const ws = new WebSocket(getChatWebSocketUrl(patientId, token));
    socketRef.current = ws;

    ws.onopen = () => {
      reconnectAttemptedRef.current = false;
      setStatus("open");
    };
    ws.onmessage = (event) => {
      const msg: ChatMessageOut = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    };
    ws.onclose = (event) => {
      // 4403 = the backend rejected access (not linked to this patient, or
      // a CareLink was revoked between page load and connect) - retrying
      // won't help, so stop rather than looping.
      if (event.code === 4403) {
        setStatus("denied");
        return;
      }
      if (!reconnectAttemptedRef.current) {
        // Most likely cause: the short-lived access token expired mid-
        // session. Re-fetching history over REST silently refreshes it
        // via apiFetch's existing 401-retry flow, then we reconnect with
        // whatever token that left in memory.
        reconnectAttemptedRef.current = true;
        setStatus("reconnecting");
        getChatHistory(patientId)
          .then(() => openSocket())
          .catch(() => setStatus("closed"));
      } else {
        setStatus("closed");
      }
    };
  }

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setHistoryLoading(true);
    getChatHistory(patientId)
      .then((history) => {
        if (cancelled) return;
        setMessages(history);
        openSocket();
      })
      .catch((e) => {
        if (!cancelled) setHistoryError(e.message || "Could not load chat history.");
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });

    return () => {
      cancelled = true;
      socketRef.current?.close();
      socketRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || socketRef.current?.readyState !== WebSocket.OPEN) return;
    socketRef.current.send(text);
    setDraft("");
  }

  const statusLabel: Record<ConnectionStatus, string> = {
    connecting: "Connecting...",
    open: "Live",
    reconnecting: "Reconnecting...",
    denied: "You no longer have access to this chat.",
    closed: "Chat disconnected - refresh the page.",
  };
  const statusColor: Record<ConnectionStatus, string> = {
    connecting: "text-ink/40",
    open: "text-sage",
    reconnecting: "text-gold",
    denied: "text-alert",
    closed: "text-alert",
  };

  return (
    <main className="min-h-screen px-6 py-10 max-w-2xl mx-auto flex flex-col">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm text-sage font-medium">CareAI · Family Chat</p>
          <h1 className="text-2xl font-display font-bold text-ink mt-0.5">Chat</h1>
        </div>
        <span className={`text-xs font-medium ${statusColor[status]}`}>{statusLabel[status]}</span>
      </header>

      {historyError && <p className="text-alert text-sm mb-4">{historyError}</p>}

      <div className="flex-1 bg-white border border-sageLight rounded-xl p-4 min-h-[400px] max-h-[520px] overflow-y-auto flex flex-col gap-3">
        {historyLoading && <p className="text-ink/40 text-sm">Loading...</p>}
        {!historyLoading && messages.length === 0 && !historyError && (
          <p className="text-ink/40 text-sm">No messages yet - say hello.</p>
        )}
        {messages.map((m) => {
          const isMine = m.sender_id === myUserId;
          return (
            <div key={m.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[75%] ${isMine ? "items-end" : "items-start"} flex flex-col`}>
                {!isMine && (
                  <p className="text-xs text-ink/40 mb-0.5 px-1">
                    {m.sender_name} <span className="capitalize">({m.sender_role})</span>
                  </p>
                )}
                <div className={`rounded-2xl px-3.5 py-2 text-sm ${isMine ? "bg-sage text-white" : "bg-sageLight text-ink"}`}>
                  {m.content}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type a message..."
          maxLength={2000}
          disabled={status !== "open"}
          className="flex-1 border border-sageLight rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sage disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={status !== "open" || !draft.trim()}
          className="bg-sage text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-sage/90 disabled:opacity-50 transition"
        >
          Send
        </button>
      </form>

      <button onClick={() => router.back()} className="inline-block mt-6 text-sm text-sage font-medium hover:underline self-start">
        Back
      </button>
    </main>
  );
}

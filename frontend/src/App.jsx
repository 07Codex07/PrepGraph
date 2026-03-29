import { useState, useEffect, useRef, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

const markdownComponents = {
  p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => <strong className="font-semibold text-zinc-100">{children}</strong>,
  ul: ({ children }) => <ul className="mb-3 ml-4 list-disc space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="mb-3 ml-4 list-decimal space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ href, children }) => (
    <a
      href={href}
      className="font-medium text-indigo-400 underline decoration-indigo-400/40 underline-offset-2 hover:text-indigo-300"
      target="_blank"
      rel="noreferrer"
    >
      {children}
    </a>
  ),
  code: ({ inline, className, children, ...props }) => {
    if (inline) {
      return (
        <code
          className="rounded-md bg-zinc-950/80 px-1.5 py-0.5 text-[0.9em] text-indigo-200 ring-1 ring-zinc-800"
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <pre className="mb-3 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-sm">
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  },
  h1: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold text-zinc-100 first:mt-0">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-2 mt-4 text-base font-semibold text-zinc-100 first:mt-0">{children}</h3>,
  h3: ({ children }) => <h3 className="mb-2 mt-3 text-sm font-semibold text-zinc-200 first:mt-0">{children}</h3>,
  blockquote: ({ children }) => (
    <blockquote className="mb-3 border-l-2 border-indigo-500/50 pl-3 text-zinc-400">{children}</blockquote>
  ),
  table: ({ children }) => (
    <div className="mb-3 overflow-x-auto rounded-lg border border-zinc-800">
      <table className="w-full text-left text-sm">{children}</table>
    </div>
  ),
  th: ({ children }) => (
    <th className="border-b border-zinc-800 bg-zinc-950/50 px-3 py-2 font-medium text-zinc-300">{children}</th>
  ),
  td: ({ children }) => <td className="border-b border-zinc-800/80 px-3 py-2 text-zinc-400">{children}</td>,
};

function MessageBubble({ role, content }) {
  const isUser = role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[min(100%,36rem)] rounded-2xl rounded-br-md bg-indigo-600 px-4 py-3 text-[15px] leading-relaxed text-white shadow-lg shadow-indigo-950/30">
          <p className="whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[min(100%,40rem)] rounded-2xl rounded-bl-md border border-zinc-800/90 bg-zinc-900/80 px-4 py-3 text-[15px] text-zinc-300 shadow-md backdrop-blur-sm">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default function App() {
  const [userId, setUserId] = useState("vinayak");
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading, scrollToBottom]);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/history/${encodeURIComponent(userId)}`);
        if (!res.ok) throw new Error("history");
        const data = await res.json();
        if (!cancelled) setChatHistory(data.history ?? []);
      } catch (e) {
        if (!cancelled) console.error("History fetch failed:", e);
      }
    };
    fetchHistory();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const sendMessage = async () => {
    const userMessage = message.trim();
    if (!userMessage || !userId.trim() || isLoading) return;

    setMessage("");
    setError("");
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, message: userMessage }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();
      setChatHistory((prev) => [...prev, { role: "assistant", content: data.assistant }]);
    } catch (err) {
      setError("Could not reach the server. Check that the API is running and try again.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = async () => {
    if (!userId.trim()) return;
    try {
      const response = await fetch(`${API_BASE}/memory/clear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (response.ok) {
        setChatHistory([]);
        setError("");
      }
    } catch (err) {
      console.error("Clear failed:", err);
    }
  };

  const onComposerInput = (e) => {
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const canSend = message.trim().length > 0 && userId.trim().length > 0 && !isLoading;

  return (
    <div className="flex h-dvh flex-col bg-zinc-950 text-zinc-100">
      <div
        className="pointer-events-none fixed inset-0 opacity-40"
        aria-hidden
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.18), transparent), radial-gradient(ellipse 60% 40% at 100% 0%, rgba(139, 92, 246, 0.08), transparent)",
        }}
      />

      <header className="relative z-10 flex-shrink-0 border-b border-zinc-800/80 bg-zinc-950/75 backdrop-blur-xl">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-4 px-4 sm:h-16 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-950/40">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold tracking-tight text-white sm:text-xl">PrepGraph</h1>
              <p className="hidden truncate text-xs text-zinc-500 sm:block">RAG assistant</p>
            </div>
          </div>

          <div className="flex flex-shrink-0 items-center gap-2 sm:gap-3">
            <label className="sr-only" htmlFor="user-id">
              User ID
            </label>
            <input
              id="user-id"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="User ID"
              className="w-[7.5rem] rounded-lg border border-zinc-700 bg-zinc-900/90 px-2.5 py-2 text-sm text-zinc-100 placeholder-zinc-600 outline-none ring-indigo-500/0 transition focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/30 sm:w-36"
            />
            <button
              type="button"
              onClick={clearChat}
              className="rounded-lg border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-sm font-medium text-zinc-300 transition hover:border-zinc-600 hover:bg-zinc-800 hover:text-white"
            >
              Clear
            </button>
          </div>
        </div>
      </header>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <main className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-6 sm:px-6">
          <div className="mx-auto flex max-w-3xl flex-col gap-6">
            {chatHistory.length === 0 && !isLoading && (
              <div className="flex flex-1 flex-col items-center justify-center py-16 text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-zinc-800 bg-zinc-900/50">
                  <svg className="h-7 w-7 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden>
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                </div>
                <h2 className="text-lg font-semibold text-zinc-200">Start a conversation</h2>
                <p className="mt-2 max-w-sm text-sm leading-relaxed text-zinc-500">
                  Messages are tied to your user ID. Ask a question and the assistant will answer using your knowledge
                  base.
                </p>
              </div>
            )}

            {chatHistory.map((msg, i) => (
              <div key={`${i}-${msg.role}-${msg.content.slice(0, 24)}`} className="message-enter">
                <MessageBubble role={msg.role} content={msg.content} />
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start message-enter">
                <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-zinc-800 bg-zinc-900/80 px-4 py-3 backdrop-blur-sm">
                  <span className="flex gap-1.5" aria-hidden>
                    <span className="typing-dot h-2 w-2 rounded-full bg-indigo-400" />
                    <span className="typing-dot h-2 w-2 rounded-full bg-indigo-400" />
                    <span className="typing-dot h-2 w-2 rounded-full bg-indigo-400" />
                  </span>
                  <span className="text-sm text-zinc-500">Thinking…</span>
                </div>
              </div>
            )}

            {error && (
              <div
                className="message-enter rounded-xl border border-red-500/25 bg-red-950/40 px-4 py-3 text-center text-sm text-red-200"
                role="alert"
              >
                {error}
              </div>
            )}

            <div ref={messagesEndRef} className="h-px shrink-0" aria-hidden />
          </div>
        </main>

        <footer className="relative z-10 flex-shrink-0 border-t border-zinc-800/80 bg-zinc-950/90 px-4 py-4 backdrop-blur-xl sm:px-6">
          <div className="mx-auto flex max-w-3xl items-end gap-3">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onInput={onComposerInput}
              onKeyDown={handleKeyDown}
              placeholder="Message…"
              rows={1}
              className="max-h-40 min-h-[48px] w-full resize-none rounded-xl border border-zinc-800 bg-zinc-900/90 px-4 py-3 text-[15px] text-zinc-100 placeholder-zinc-600 outline-none ring-indigo-500/0 transition focus:border-indigo-500/40 focus:ring-2 focus:ring-indigo-500/25"
              style={{ maxHeight: 160, minHeight: 48 }}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={!canSend}
              className="flex h-12 flex-shrink-0 items-center justify-center rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white shadow-lg shadow-indigo-950/30 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500 disabled:shadow-none"
            >
              Send
            </button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-zinc-600">Enter to send · Shift+Enter for new line</p>
        </footer>
      </div>
    </div>
  );
}

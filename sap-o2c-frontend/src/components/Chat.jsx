import { useEffect, useMemo, useRef, useState } from "react";
import GraphView from "./GraphView";

const API_URL = "http://127.0.0.1:8000/query";

const SUGGESTED_QUERIES = [
  "Trace order 740506",
  "Find orders without invoices",
  "Show full flow for invoice 90504298",
];

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

function toClipboardText(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
}

function humanSummary(message) {
  if (message.role !== "assistant") return "";
  const data = message.payload ?? {};
  const type = message.queryType || "result";

  if (type === "trace_order") {
    const path = Array.isArray(data.path) ? data.path : [];
    const nodes = path.map((item) => item.id ?? item.node).filter(Boolean);
    return nodes.length
      ? `Traced the order flow across ${nodes.length} nodes: ${nodes.join(" → ")}.`
      : data.found === false
        ? `No flow was found for order ${data.order_id ?? "this order"}.`
        : "Traced the order flow.";
  }

  if (type === "trace_invoice") {
    const path = Array.isArray(data.path) ? data.path : [];
    const nodes = path.map((item) => item.id ?? item.node).filter(Boolean);
    return nodes.length
      ? `Traced the invoice flow across ${nodes.length} nodes: ${nodes.join(" → ")}.`
      : data.found === false
        ? `No flow was found for invoice ${data.invoice_id ?? "this invoice"}.`
        : "Traced the invoice flow.";
  }

  if (type === "find_orders_without_invoices") {
    const count = typeof data.count === "number" ? data.count : 0;
    return count
      ? `Found ${count} order${count === 1 ? "" : "s"} without invoices.`
      : "No orders without invoices were found.";
  }

  if (type === "unsupported") {
    return "This system only answers questions about the dataset.";
  }

  if (type === "error") {
    return "There was an error while fetching the response.";
  }

  return "Here is the structured result from the dataset query.";
}

function prettyJson(value) {
  if (value == null) return {};
  return value;
}

function EmptyState({ onPick }) {
  return (
    <div className="flex min-h-full items-center justify-center px-4 py-10">
      <div className="max-w-xl rounded-[30px] border border-slate-700/50 bg-slate-900/60 px-8 py-10 text-center shadow-2xl shadow-black/30 backdrop-blur-2xl">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/10 shadow-lg shadow-cyan-500/10">
          <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-cyan-300 to-blue-500" />
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-white">
          Ask something like:
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          Trace order 740506, show full flow for invoice 90504298, or find
          orders without invoices.
        </p>

        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {SUGGESTED_QUERIES.map((query) => (
            <button
              key={query}
              type="button"
              onClick={() => onPick(query)}
              className="rounded-full border border-slate-700/60 bg-slate-950/60 px-4 py-2 text-xs font-medium text-slate-200 transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-400/40 hover:text-white"
            >
              {query}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SkeletonMessage({ side = "left" }) {
  return (
    <div
      className={`flex w-full animate-pulse ${
        side === "right" ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`max-w-[75%] rounded-2xl border border-slate-700/60 bg-slate-900/60 px-4 py-3 shadow-xl shadow-black/20 ${
          side === "right" ? "bg-gradient-to-br from-cyan-400/20 to-blue-500/20" : ""
        }`}
      >
        <div className="h-3 w-20 rounded-full bg-slate-700/70" />
        <div className="mt-3 space-y-2">
          <div className="h-3 w-56 rounded-full bg-slate-700/50" />
          <div className="h-3 w-44 rounded-full bg-slate-700/50" />
        </div>
      </div>
    </div>
  );
}

function JsonSyntax({ data }) {
  const json = useMemo(() => JSON.stringify(data, null, 2), [data]);

  const tokens = useMemo(() => {
    const parts = [];
    const regex =
      /("(?:\\.|[^"\\])*"(?=\s*:))|("(?:\\.|[^"\\])*")|(\b\d+(?:\.\d+)?\b)|(\btrue\b|\bfalse\b|\bnull\b)|([{}\[\],:])/g;

    let lastIndex = 0;
    let match;

    while ((match = regex.exec(json)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: "text", value: json.slice(lastIndex, match.index) });
      }

      if (match[1]) {
        parts.push({ type: "key", value: match[1] });
      } else if (match[2]) {
        parts.push({ type: "string", value: match[2] });
      } else if (match[3]) {
        parts.push({ type: "number", value: match[3] });
      } else if (match[4]) {
        parts.push({ type: "literal", value: match[4] });
      } else if (match[5]) {
        parts.push({ type: "punct", value: match[5] });
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < json.length) {
      parts.push({ type: "text", value: json.slice(lastIndex) });
    }

    return parts;
  }, [json]);

  const classNameByType = {
    key: "text-cyan-300",
    string: "text-emerald-300",
    number: "text-amber-300",
    literal: "text-fuchsia-300",
    punct: "text-slate-500",
    text: "text-slate-200",
  };

  return (
    <pre className="overflow-x-auto rounded-2xl border border-slate-700/60 bg-slate-950/70 p-4 text-[13px] leading-6 text-slate-200 shadow-inner shadow-black/20">
      <code className="font-mono">
        {tokens.map((token, index) => (
          <span key={index} className={classNameByType[token.type] || "text-slate-200"}>
            {token.value}
          </span>
        ))}
      </code>
    </pre>
  );
}

function MessageBubble({ message, onCopy }) {
  const isUser = message.role === "user";
  const timeLabel = formatTime(message.timestamp);
  const summary = isUser ? "" : humanSummary(message);

  return (
    <div
      className={`flex w-full transition-all duration-300 ease-out ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`group flex max-w-[75%] flex-col gap-2 ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        <div className="flex items-center gap-2 px-1 text-[11px] text-slate-500">
          <span className="font-medium uppercase tracking-[0.22em]">
            {isUser ? "You" : "Assistant"}
          </span>
          {timeLabel ? <span>• {timeLabel}</span> : null}
        </div>

        <div
          className={`rounded-2xl border px-4 py-3 shadow-xl transition-all duration-200 ${
            isUser
              ? "border-cyan-400/20 bg-gradient-to-br from-cyan-400 to-blue-500 text-slate-950 shadow-cyan-950/30"
              : "border-slate-700/60 bg-slate-900/70 text-slate-100 backdrop-blur-xl shadow-black/30"
          }`}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap break-words text-[15px] leading-7 text-slate-950">
              {message.text}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-300">
                    {message.queryType || "result"}
                  </span>
                  {summary ? (
                    <span className="text-sm leading-6 text-slate-300">{summary}</span>
                  ) : null}
                </div>

                {onCopy ? (
                  <button
                    type="button"
                    onClick={() => onCopy(message.payload)}
                    className="rounded-full border border-slate-700/80 bg-slate-950/70 px-3 py-1 text-[11px] font-medium text-slate-300 transition hover:border-cyan-400/40 hover:text-white active:scale-95"
                  >
                    Copy
                  </button>
                ) : null}
              </div>

              <details className="group rounded-2xl border border-slate-700/50 bg-slate-950/50 p-4">
                <summary className="cursor-pointer list-none text-sm font-medium text-slate-200 transition hover:text-cyan-200">
                  <span className="inline-flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.9)]" />
                    Structured JSON
                  </span>
                  <span className="ml-2 text-xs text-slate-500 group-open:hidden">
                    click to expand
                  </span>
                  <span className="ml-2 hidden text-xs text-slate-500 group-open:inline">
                    click to collapse
                  </span>
                </summary>
                <div className="mt-3">
                  <JsonSyntax data={prettyJson(message.payload)} />
                </div>
              </details>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [showScrollButton, setShowScrollButton] = useState(false);

  const scrollRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    if (!toast) return;
    const id = window.setTimeout(() => setToast(""), 1800);
    return () => window.clearTimeout(id);
  }, [toast]);

  function handleScroll(e) {
    const el = e.currentTarget;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    setShowScrollButton(distanceFromBottom > 260);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: trimmed, timestamp: new Date().toISOString() },
    ]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });

      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          queryType: data.query_type,
          payload: data.result ?? { answer: data.answer },
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      setToast("Unable to reach the backend API");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          queryType: "error",
          payload: { error: "Unable to reach the backend API." },
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy(payload) {
    navigator.clipboard.writeText(toClipboardText(payload)).then(() => {
      setToast("Copied to clipboard");
    });
  }

  function scrollToBottom() {
    scrollRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }

  function applySuggested(query) {
    if (loading) return;
    setQuestion(query);
  }

  const emptyState = messages.length === 0 && !loading;

  return (
    <section className="relative mx-auto flex h-full w-full max-w-[900px] flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-x-10 top-6 h-40 rounded-full bg-cyan-400/10 blur-3xl" />

      {toast ? (
        <div className="absolute right-6 top-6 z-30 rounded-full border border-cyan-400/20 bg-slate-950/85 px-4 py-2 text-xs font-medium text-cyan-200 shadow-xl shadow-black/30 backdrop-blur-xl">
          {toast}
        </div>
      ) : null}

      <div
        ref={listRef}
        onScroll={handleScroll}
        className="relative flex-1 overflow-y-auto px-4 pb-6 pt-6 sm:px-6 lg:px-8"
      >
        {emptyState ? (
          <EmptyState onPick={applySuggested} />
        ) : (
          <div className="space-y-5 pb-2">
            {messages.map((message, index) => (
              <div key={`${message.role}-${index}`} className="space-y-3">
                <MessageBubble
                  message={message}
                  onCopy={message.role === "assistant" ? handleCopy : undefined}
                />
                {message.role === "assistant" && Array.isArray(message.payload?.path) ? (
                  <GraphView path={message.payload.path} />
                ) : null}
              </div>
            ))}

            {loading ? (
              <>
                <SkeletonMessage side="right" />
                <SkeletonMessage side="left" />
                <div className="flex w-full justify-start">
                  <div className="max-w-[75%] rounded-2xl border border-slate-700/60 bg-slate-900/70 px-4 py-3 shadow-xl shadow-black/30 backdrop-blur-xl">
                    <div className="mb-2 flex items-center gap-2 text-[11px] uppercase tracking-[0.22em] text-cyan-300">
                      <span>AI is thinking...</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-cyan-300/80 [animation-delay:-0.18s]" />
                      <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-cyan-300/80 [animation-delay:-0.09s]" />
                      <span className="h-2.5 w-2.5 animate-bounce rounded-full bg-cyan-300/80" />
                    </div>
                  </div>
                </div>
              </>
            ) : null}

            <div ref={scrollRef} />
          </div>
        )}
      </div>

      <div className="relative shrink-0 px-4 pb-4 sm:px-6 lg:px-8">
        {showScrollButton ? (
          <button
            type="button"
            onClick={scrollToBottom}
            className="absolute -top-14 right-8 rounded-full border border-slate-700/60 bg-slate-900/90 px-4 py-2 text-xs font-medium text-slate-200 shadow-xl shadow-black/30 transition-all duration-200 hover:-translate-y-0.5 hover:border-cyan-400/40 hover:text-white active:scale-95"
          >
            Scroll to latest
          </button>
        ) : null}

        <form
          onSubmit={handleSubmit}
          className="rounded-[28px] border border-slate-700/50 bg-slate-900/65 p-3 shadow-2xl shadow-black/30 backdrop-blur-2xl"
        >
          <div className="flex items-end gap-3 rounded-[24px] border border-slate-700/50 bg-slate-950/60 px-4 py-3 shadow-inner shadow-black/10 transition-all duration-200 focus-within:border-cyan-400/30 focus-within:shadow-[0_0_0_1px_rgba(34,211,238,0.16),0_0_30px_rgba(34,211,238,0.12)]">
            <div className="flex-1">
              <label htmlFor="question" className="sr-only">
                Ask a question
              </label>
              <input
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Ask something like: Trace order 740506"
                className="h-12 w-full bg-transparent text-[15px] text-white outline-none placeholder:text-slate-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="inline-flex h-12 items-center justify-center rounded-full bg-gradient-to-r from-cyan-400 to-blue-500 px-6 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-500/20 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-cyan-500/30 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Thinking..." : "Send"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

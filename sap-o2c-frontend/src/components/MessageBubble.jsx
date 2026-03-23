import JsonViewer from "./JsonViewer";

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function MessageBubble({ message, onCopy }) {
  const isUser = message.role === "user";
  const timeLabel = formatTime(message.timestamp);

  return (
    <div
      className={`flex w-full animate-[messageIn_240ms_ease-out] ${
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
          {!isUser ? (
            <div className="mb-3 flex items-start justify-between gap-4">
              <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-300">
                {message.queryType || "result"}
              </span>

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
          ) : null}

          {isUser ? (
            <div className="whitespace-pre-wrap break-words text-[15px] leading-7 text-slate-950">
              {message.text}
            </div>
          ) : (
            <JsonViewer data={message.payload} />
          )}
        </div>
      </div>
    </div>
  );
}

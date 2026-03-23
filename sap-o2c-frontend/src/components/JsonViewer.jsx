function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderValue(value, level = 0) {
  const pad = 16;
  const indent = level * pad;

  if (value === null) {
    return <span className="text-violet-300">null</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-slate-500">[]</span>;
    return (
      <div className="space-y-1">
        <span className="text-slate-500">[</span>
        <div className="space-y-1">
          {value.map((item, index) => (
            <div key={index} style={{ paddingLeft: indent + pad }} className="leading-6">
              {renderValue(item, level + 1)}
              {index < value.length - 1 ? <span className="text-slate-500">,</span> : null}
            </div>
          ))}
        </div>
        <span className="text-slate-500">]</span>
      </div>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value);
    if (entries.length === 0) {
      return <span className="text-slate-500">{`{}`}</span>;
    }

    return (
      <div className="space-y-1">
        <span className="text-slate-500">{`{`}</span>
        <div className="space-y-1">
          {entries.map(([key, item], index) => (
            <div key={key} style={{ paddingLeft: indent + pad }} className="leading-6">
              <span className="text-cyan-300">{escapeHtml(`"${key}"`)}</span>
              <span className="text-slate-500">: </span>
              {renderValue(item, level + 1)}
              {index < entries.length - 1 ? <span className="text-slate-500">,</span> : null}
            </div>
          ))}
        </div>
        <span className="text-slate-500">{`}`}</span>
      </div>
    );
  }

  if (typeof value === "string") {
    return <span className="text-emerald-300">{escapeHtml(`"${value}"`)}</span>;
  }

  if (typeof value === "number") {
    return <span className="text-amber-300">{String(value)}</span>;
  }

  if (typeof value === "boolean") {
    return <span className="text-fuchsia-300">{String(value)}</span>;
  }

  return <span className="text-slate-200">{escapeHtml(String(value))}</span>;
}

export default function JsonViewer({ data }) {
  return (
    <pre className="overflow-x-auto rounded-2xl border border-slate-700/60 bg-slate-950/70 p-4 text-[13px] leading-6 text-slate-200 shadow-inner shadow-black/20">
      <code className="font-mono">{renderValue(data)}</code>
    </pre>
  );
}

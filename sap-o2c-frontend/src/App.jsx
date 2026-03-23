import Chat from "./components/Chat";

export default function App() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.14),_transparent_28%),linear-gradient(180deg,#020617_0%,#0f172a_45%,#020617_100%)] text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(148,163,184,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.05)_1px,transparent_1px)] bg-[size:80px_80px] opacity-20" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-cyan-400/40" />
      <div className="pointer-events-none absolute left-1/2 top-24 h-80 w-80 -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl" />

      <div className="relative mx-auto flex min-h-screen w-full max-w-[1100px] flex-col px-4 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 border-b border-slate-700/40 py-5 backdrop-blur-sm">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-300/80">
              SAP O2C Intelligence
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
              SAP O2C AI Assistant
            </h1>
          </div>

          <div className="hidden items-center gap-2 rounded-full border border-slate-700/60 bg-slate-900/50 px-4 py-2 text-xs font-medium text-slate-300 shadow-lg shadow-black/20 sm:flex">
            <span className="h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_14px_rgba(34,211,238,0.9)]" />
            Connected to backend
          </div>
        </header>

        <main className="flex min-h-0 flex-1 overflow-hidden">
          <Chat />
        </main>
      </div>
    </div>
  );
}

import { useMemo } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";

const TYPE_STYLES = {
  Customer: { bg: "#0ea5e9", border: "#38bdf8", text: "#020617" },
  Order: { bg: "#22c55e", border: "#4ade80", text: "#020617" },
  Delivery: { bg: "#f59e0b", border: "#fbbf24", text: "#020617" },
  Invoice: { bg: "#ef4444", border: "#f87171", text: "#ffffff" },
  Payment: { bg: "#14b8a6", border: "#2dd4bf", text: "#020617" },
  Default: { bg: "#334155", border: "#475569", text: "#e2e8f0" },
};

function getTypeStyle(type) {
  return TYPE_STYLES[type] || TYPE_STYLES.Default;
}

function nodeLabel(node) {
  return node?.id ?? node?.node ?? "";
}

export default function GraphView({ path = [] }) {
  const { nodes, edges } = useMemo(() => {
    const valid = Array.isArray(path) ? path.filter(Boolean) : [];

    const nodes = valid.map((item, index) => {
      const type = item.type || "Default";
      const label = nodeLabel(item);
      const style = getTypeStyle(type);

      return {
        id: item.node || `${type}-${label}-${index}`,
        type: "default",
        position: { x: index * 170, y: 0 },
        data: {
          type,
          label: (
            <div className="flex flex-col items-center gap-1">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] opacity-80">
                {type}
              </div>
              <div className="text-sm font-semibold">{label}</div>
            </div>
          ),
        },
        style: {
          minWidth: 130,
          padding: "12px 14px",
          borderRadius: 18,
          background: `linear-gradient(135deg, ${style.bg} 0%, ${style.border} 100%)`,
          color: style.text,
          border: `1px solid ${style.border}55`,
          boxShadow: "0 18px 40px rgba(2, 6, 23, 0.35)",
        },
      };
    });

    const edges = valid.slice(1).map((item, index) => ({
      id: `e-${index}`,
      source: valid[index].node || `${valid[index].type}-${nodeLabel(valid[index])}-${index}`,
      target: item.node || `${item.type}-${nodeLabel(item)}-${index + 1}`,
      animated: true,
      type: "smoothstep",
      style: {
        stroke: "#22d3ee",
        strokeWidth: 2,
      },
      markerEnd: {
        type: "arrowclosed",
        color: "#22d3ee",
      },
    }));

    return { nodes, edges };
  }, [path]);

  if (!Array.isArray(path) || path.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 overflow-hidden rounded-2xl border border-slate-700/60 bg-slate-950/60 shadow-xl shadow-black/30 backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-slate-800/70 px-4 py-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-300">
            Graph View
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Interactive flow extracted from the API response path
          </p>
        </div>
      </div>

      <div className="h-[280px] w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          panOnDrag
          zoomOnScroll
          zoomOnPinch
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={18} size={1} color="rgba(148,163,184,0.18)" />
          <MiniMap
            zoomable
            pannable
            nodeStrokeColor={(n) => getTypeStyle(n.data?.type).border}
            nodeColor={(n) => getTypeStyle(n.data?.type).bg}
          />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}

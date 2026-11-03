import type { ModelDescriptionOut } from "../generated/wire";

const KIND_CLASS: Record<string, string> = {
  INPUT: "k-io", INPUT_SPEC: "k-spec", ASSERT: "k-spec", DENSE: "k-lin", CONV2D: "k-lin",
  RELU: "k-act", AVGPOOL2D: "k-pool", FLATTEN: "k-shape",
};

/** Layered DAG: depth = longest path from a source; edges follow ACT preds. */
export function layout(model: ModelDescriptionOut): Map<number, { depth: number; row: number }> {
  const depth = new Map<number, number>();
  for (const l of model.layers) depth.set(l.layer_id, Math.max(0, ...l.preds.map((p) => (depth.get(p) ?? 0) + 1)));
  const rows = new Map<number, number>();
  const pos = new Map<number, { depth: number; row: number }>();
  for (const l of model.layers) {
    const d = depth.get(l.layer_id)!;
    const r = rows.get(d) ?? 0;
    rows.set(d, r + 1);
    pos.set(l.layer_id, { depth: d, row: r });
  }
  return pos;
}

export function ModelGraph({ model, selectedLayer, onSelectLayer }: {
  model: ModelDescriptionOut; selectedLayer: number | null; onSelectLayer: (id: number) => void;
}) {
  const pos = layout(model);
  // Left to right: depth along x, siblings stacked along y.
  const W = 150, H = 44, GX = 36, GY = 14;
  const maxDepth = Math.max(...[...pos.values()].map((p) => p.depth));
  const maxRow = Math.max(...[...pos.values()].map((p) => p.row));
  const width = (maxDepth + 1) * (W + GX) + GX;
  const height = (maxRow + 1) * (H + GY) + GY;
  const xy = (id: number) => {
    const p = pos.get(id)!;
    return { x: GX + p.depth * (W + GX), y: GY + p.row * (H + GY) };
  };
  return (
    <div className="graphwrap">
      <svg className="graph" viewBox={`0 0 ${width} ${height}`} width={width} height={height} role="img" aria-label="network DAG">
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" className="arrowhead" />
          </marker>
        </defs>
        {model.layers.flatMap((l) => l.preds.map((p) => {
          const a = xy(p), b = xy(l.layer_id);
          return <path key={`${p}-${l.layer_id}`} className="edge" markerEnd="url(#arrow)"
            d={`M${a.x + W},${a.y + H / 2} C${a.x + W + GX / 2},${a.y + H / 2} ${b.x - GX / 2},${b.y + H / 2} ${b.x},${b.y + H / 2}`} />;
        }))}
        {model.layers.map((l) => {
          const { x, y } = xy(l.layer_id);
          const active = l.layer_id === selectedLayer;
          return (
            <g key={l.layer_id} className={`node ${KIND_CLASS[l.kind] ?? "k-other"}${active ? " selected" : ""}`}
              transform={`translate(${x},${y})`} onClick={() => onSelectLayer(l.layer_id)} role="button" tabIndex={0}
              onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && onSelectLayer(l.layer_id)}>
              <title>{`layer ${l.layer_id} ${l.kind}: ${l.in_vars} in → ${l.out_vars} out`}</title>
              <rect width={W} height={H} rx={8} />
              <text x={10} y={19} className="nkind">{l.kind}</text>
              <text x={10} y={35} className="nsub">#{l.layer_id} · {l.in_vars}→{l.out_vars}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

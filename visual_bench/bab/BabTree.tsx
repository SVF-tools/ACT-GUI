// Node-link view of the BaB search tree as ACT had committed it by the shown wave.
import { useEffect, useMemo, useRef } from "react";
import type { BabNodeOut, BabTerminalOut } from "../generated/wire";
import { fmt, num } from "../shared/wire";
import { changedAt, describeBranch, layout, STATE_LABEL, stateAt } from "./tree";
import { useWidth } from "./useWidth";

const PAD_X = 30, PAD_TOP = 16, PAD_BOTTOM = 22, MIN_SLOT = 7.5, MAX_SLOT = 40, LEVEL = 46;

export function BabTree({ nodes, root, wave, terminal, selected, onSelect, specRows }: {
  nodes: BabNodeOut[]; root: number; wave: number; terminal: BabTerminalOut | null; selected: number | null;
  onSelect: (id: number) => void; specRows?: number;
}) {
  const [ref, width] = useWidth();
  const centered = useRef<number | null>(null);
  const { placed, slots, depth } = useMemo(() => layout(nodes, root), [nodes, root]);
  const slot = Math.min(MAX_SLOT, Math.max(MIN_SLOT, (width - 2 * PAD_X) / Math.max(1, slots)));
  const r = Math.min(7, Math.max(3.5, slot * 0.3));
  const svgWidth = Math.max(width, 2 * PAD_X + slots * slot);
  const offset = (svgWidth - slots * slot) / 2;
  const at = new Map(placed.map((p) => [p.node.node_id, { x: offset + (p.x + 0.5) * slot, y: PAD_TOP + r + p.depth * LEVEL, p }]));
  const height = PAD_TOP + 2 * r + depth * LEVEL + PAD_BOTTOM;
  // A tree wider than the panel opens centered on its root once per focus, then keeps the user's scroll position.
  useEffect(() => {
    const top = at.get(root);
    if (!ref.current || !top || width === 0 || centered.current === root) return;
    centered.current = root;
    ref.current.scrollLeft = Math.max(0, top.x - width / 2);
  });
  const onPath = new Set<number>();
  for (let id = selected; id !== null && at.has(id) && !onPath.has(id); id = at.get(id)!.p.node.parent_id) onPath.add(id);
  const shown = placed.flatMap((p) => {
    const state = stateAt(p.node, wave, terminal);
    return state === null ? [] : [{ ...p, state, pos: at.get(p.node.node_id)! }];
  });
  return (
    <div className="babtree" ref={ref}>
      {width > 0 && (
        <svg width={svgWidth} height={height} role="group" aria-label={`BaB search tree at wave ${wave}`}>
          {Array.from({ length: depth + 1 }, (_, d) => (
            <text key={d} className="babdepth" x={4} y={PAD_TOP + r + d * LEVEL + 4}>{d === 0 && root !== 0 ? "focus" : `d${d}`}</text>
          ))}
          {shown.map(({ node, state, pos }) => {
            const parent = at.get(node.parent_id);
            if (!parent || node.node_id === root) return null;
            return <line key={`e${node.node_id}`} className={`babedge s-${state}${onPath.has(node.node_id) ? " path" : ""}`} x1={parent.x} y1={parent.y + r}
              x2={pos.x} y2={pos.y - r} />;
          })}
          {shown.map(({ node, state, pos }) => {
            const fresh = changedAt(node, wave, terminal);
            const bound = node.bound === null || node.solved_wave === null || node.solved_wave > wave ? "" : ` · bound ${fmt(num(node.bound), 4)}`;
            return (
              <g key={node.node_id} className={`babnode s-${state}${fresh ? " fresh" : ""}${selected === node.node_id ? " sel" : ""}`}
                transform={`translate(${pos.x},${pos.y})`} onClick={() => onSelect(node.node_id)}>
                <title>{`#${node.node_id} · ${STATE_LABEL[state]} · depth ${node.depth}${bound}\n${describeBranch(node.branch, specRows)}`}</title>
                <circle className="babhit" r={Math.max(r + 3, Math.min(slot / 2, 11))} />
                {fresh && <circle key={`f${wave}`} className="babhalo" r={r + 4} />}
                <circle className="babdot" r={node.node_id === root ? r + 1.5 : r} />
                {selected === node.node_id && <circle className="babring" r={r + 3.5} />}
                {(node.hidden_children ?? 0) > 0 && <text className="babmore" y={r + 13}>+{node.hidden_children}</text>}
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}

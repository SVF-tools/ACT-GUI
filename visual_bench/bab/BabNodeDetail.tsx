// One BaB node as ACT recorded it: outcome and bound, the splits on its path, its children, per-layer bounds.
import type { BabLayerOut, BabNodeOut, ModelDescriptionOut } from "../generated/wire";
import { fmt, num } from "../shared/wire";
import { Pixels, specImageShape } from "../shared/ui/pixels";
import { useBabNode } from "./hooks";
import { boxWidths, describeBranch, STATE_LABEL } from "./tree";

const BOUND_KIND: Record<string, string> = {
  certified_node_lower_bound: "certified lower bound of the node's property margin",
  negative_max_constraint_violation: "minus the largest constraint violation (LP tier)",
};

export function BabNodeDetail({ runId, nodeId, model, onSelect, onFocus, focusRoot }: {
  runId: string; nodeId: number; model: ModelDescriptionOut; onSelect: (id: number) => void; onFocus: (id: number) => void;
  focusRoot: number;
}) {
  const q = useBabNode(runId, nodeId);
  if (q.status === "error") return <div className="error">{q.error.message}</div>;
  if (!q.data) return <div className="note">Loading node #{nodeId}…</div>;
  const { node, layers, path, children, solve_status, bound_kind } = q.data;
  const specRows = model.output_spec?.rows;
  const relu = layers.filter((l) => l.unstable !== null);
  return (
    <div className="babdetail">
      <div className="babdetailhead">
        <h4>Node #{node.node_id}</h4>
        <span className={`chip babchip s-${node.state}`}>{STATE_LABEL[node.state]}</span>
        <span className="muted">depth {node.depth}</span>
        {node.children > 0 && node.node_id !== focusRoot &&
          <button type="button" className="secondary small" onClick={() => onFocus(node.node_id)}>Focus subtree</button>}
      </div>
      <div className="kv">
        <span>ACT outcome</span><b>{node.outcome ?? (node.state === "falsified" ? "counterexample (ACT's terminal record)" : "not solved yet")}</b>
        {solve_status && <><span>bound problem</span><b>{solve_status}</b></>}
        {node.bound !== null && <><span>bound</span><b>
          <span className="mono">{fmt(num(node.bound), 5)}</span> <small className="muted">{BOUND_KIND[bound_kind ?? ""] ?? bound_kind}</small></b></>}
        <span>waves</span><b>created {node.created_wave}{node.solved_wave !== null ? ` · solved ${node.solved_wave}` : ""}
          {node.evicted_wave !== null ? ` · evicted ${node.evicted_wave}` : ""}</b>
        <span>subtree</span><b>{node.children} children · {node.descendants} descendants</b>
      </div>
      <h4>Splits from the root</h4>
      <ol className="babpath">
        {[...path, node].map((step) => (
          <li key={step.node_id}>
            <button type="button" className={`babstep${step.node_id === node.node_id ? " here" : ""}`} onClick={() => onSelect(step.node_id)}>
              <i className={`babdotkey s-${step.state}`} />#{step.node_id}
            </button>
            <span className="mono">{describeBranch(step.branch, specRows)}</span>
          </li>
        ))}
      </ol>
      {children.length > 0 && <>
        <h4>Children</h4>
        <div className="chips">
          {children.map((c) => (
            <button key={c.node_id} type="button" className={`chip link babchip s-${c.state}`} onClick={() => onSelect(c.node_id)}
              title={describeBranch(c.branch, specRows)}>#{c.node_id} {STATE_LABEL[c.state]}</button>
          ))}
        </div>
      </>}
      <InputBox model={model} path={[...path, node]} />
      {layers.length > 0 ? <>
        <h4>Bounds at this node <small>{relu.length ? "ReLU inputs: active / inactive / unstable" : "per layer"}</small></h4>
        <div className="tblwrap">
          <table className="tbl babtbl">
            <thead><tr><th>layer</th><th>neurons</th><th>range</th><th>ReLU inputs</th></tr></thead>
            <tbody>{layers.map((l) => <LayerRow key={l.layer_id} layer={l} />)}</tbody>
          </table>
        </div>
      </> : <p className="note">{node.solved_wave === null ? "ACT reports per-layer bounds once it solves the node."
        : "ACT reported no per-layer bounds for this node."}</p>}
    </div>
  );
}

function LayerRow({ layer }: { layer: BabLayerOut }) {
  const range = (v: BabLayerOut["lb_min"]) => (v === null ? "unbounded" : fmt(num(v), 3));
  const { active, inactive, unstable } = layer;
  return (
    <tr>
      <td>L{layer.layer_id} <span className="muted">{layer.kind}</span></td>
      <td className="mono">{layer.neurons}</td>
      <td className="mono">[{range(layer.lb_min)}, {range(layer.ub_max)}]</td>
      <td>{unstable === null || active === null || inactive === null ? <span className="muted">—</span> : (
        <span className="babstab" title={`${active} active, ${inactive} inactive, ${unstable} unstable`}>
          <span className="babstabbar" aria-hidden="true">
            <i className="s-proved" style={{ flexGrow: active }} />
            <i className="s-evicted" style={{ flexGrow: inactive }} />
            <i className="s-pending" style={{ flexGrow: unstable }} />
          </span>
          <span className="mono">{active}/{inactive}/{unstable}</span>
        </span>
      )}</td>
    </tr>
  );
}

// For image inputs: how wide this node's input box is per pixel, after the input splits on its path.
function InputBox({ model, path }: { model: ModelDescriptionOut; path: BabNodeOut[] }) {
  const spec = model.input_specs[0];
  if (!spec?.lb || !spec.ub || !path.some((n) => n.branch?.kind === "input_axis")) return null;
  const shape = specImageShape(spec.shape, spec.dataset);
  if (!shape || shape.c * shape.h * shape.w !== spec.lb.length) return null;
  const lb = spec.lb.map(num), ub = spec.ub.map(num);
  const { widths, split } = boxWidths(lb, ub, path.map((n) => n.branch));
  const root = Math.max(...lb.map((l, k) => ub[k]! - l));
  return (
    <>
      <h4>Input box <small>{split} pixel{split === 1 ? "" : "s"} split on this path</small></h4>
      <Pixels xs={widths} shape={shape} lo={0} hi={root || 1} mode="heat" size="big"
        label="per-pixel width; darker = narrower" title="Width of this node's input interval per pixel, relative to the widest input interval of the property" />
    </>
  );
}

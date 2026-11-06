import { fmt, num } from "../shared/wire";
import type { FuzzingOut, ModelDescriptionOut } from "../generated/wire";
import { Pixels } from "../shared/ui/pixels";
import { inputBox, modelShape, finiteRange, argmax, vec } from "./presentation";
import { useBatchRows } from "../model_spec/hooks";

export function FuzzInputs({ f, model }: { f: FuzzingOut; model: ModelDescriptionOut | null }) {
  const seeds = f.seeds ?? [];
  const batch = useBatchRows(model?.model_id ?? null);
  const d = seeds[0]?.input.length ?? f.counterexamples[0]?.input.length ?? model?.input_dim ?? 0;
  const box = inputBox(model, d);
  const shape = modelShape(model, d);
  const perRow = new Map<number, number>(), expected = new Map<number, number>();
  for (const c of f.counterexamples) {
    perRow.set(c.spec_row, (perRow.get(c.spec_row) ?? 0) + 1);
    if (c.true_class !== null) expected.set(c.spec_row, c.true_class);
  }
  const widths = box ? box.ub.map((u, i) => u - box.lb[i]!) : [];
  const [wlo, whi] = finiteRange(widths);
  const [xlo, xhi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange(seeds.flatMap((s) => s.input.map(num)));
  return (
    <>
      <h3>Inputs <small>seeds are the model's INPUT rows; outputs from ACT's model forward{seeds.length > 1 ? ` · ${seeds.length} rows, scroll to see all` : ""}</small></h3>
      <p className="note">
        {d} input dims{shape ? ` (drawn as ${shape.c}×${shape.h}×${shape.w})` : ""}
        {box ? ` · input box width ${wlo === whi ? fmt(wlo) : `${fmt(wlo)}…${fmt(whi)}`}, values in [${fmt(xlo)}, ${fmt(xhi)}]` : ""}
        {model?.output_spec ? ` · property: ${model.output_spec.text}` : ""}
      </p>
      {seeds.length === 0 ? <div className="note">This record has no seed outputs (written before they were captured). Re-run to see them.</div> : (
        <div className="tblwrap rowscroll"><table className="tbl">
          <thead><tr><th>row</th><th>input</th>{box && <th title="seed lies inside INPUT_SPEC">in box</th>}<th>output y</th>{expected.size > 0 && <><th>argmax</th><th>expected</th></>}<th>counterexamples</th></tr></thead>
          <tbody>
            {seeds.map((s) => {
              const x = s.input.map(num), y = s.output.map(num), p = argmax(y), e = expected.get(s.row);
              const inside = box && x.every((v, i) => box.lb[i]! <= v && v <= box.ub[i]!);
              return (
                <tr key={s.row}>
                  <td className="mono" title={batch?.labels[s.row]}>{s.row}{batch ? <span className="muted clamp"> {batch.labels[s.row]}</span> : null}</td>
                  <td>{shape ? <Pixels xs={x} shape={shape} lo={xlo} hi={xhi} label="" /> : <span className="mono">{vec(x, 6)}</span>}</td>
                  {box && <td className={inside ? "mono" : "mono state warn"}>{inside ? "yes" : "no"}</td>}
                  <td className="mono">{vec(y, 6)}</td>
                  {expected.size > 0 && <><td className="mono">{p}</td><td className={e !== undefined && e !== p ? "mono state bad" : "mono"}>{e ?? "—"}</td></>}
                  <td className={perRow.get(s.row) ? "mono state bad" : "mono"}>{perRow.get(s.row) ?? 0}</td>
                </tr>
              );
            })}
          </tbody>
        </table></div>
      )}
    </>
  );
}

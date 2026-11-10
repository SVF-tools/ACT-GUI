import { useMemo, useState } from "react";
import { fmt, tooLarge } from "../shared/wire";
import type { SavedCounterexampleOut, ModelDescriptionOut } from "../generated/wire";
import { classLabel, downloadBlob, imagePng, Pixels } from "../shared/ui/pixels";
import { analyze, inputBox, modelShape, finiteRange, type Ce } from "./presentation";
import { DeltaBars } from "./DeltaBars";
import { savedCounterexampleUrl } from "./api";

// Counterexamples the user saved on this run, each exportable as a VNN-COMP counterexample file and, for images, a PNG.
export function FuzzSaved({ runId, items, model }: { runId: string; items: SavedCounterexampleOut[]; model: ModelDescriptionOut | null }) {
  const list = useMemo(() => items.map((s) => ({ s, a: analyze(s.counterexample) })), [items]);
  const d = list[0]!.a.x.length, box = inputBox(model, d), shape = modelShape(model, d);
  const ds = model?.input_specs[0]?.dataset ?? null;
  const [lo, hi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange(list.flatMap(({ a }) => [...a.x, ...a.seed]));
  const [err, setErr] = useState<string | null>(null);
  async function png(a: Ce) {
    setErr(null);
    try {
      downloadBlob(await imagePng(a.x, shape!, lo, hi), `${runId}-ce${a.ce.index}.png`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }
  return (
    <>
      <h3>Saved counterexamples <small>{items.length} on this run's record · export ACT's counterexample input</small></h3>
      <div className="cegrid">
        {list.map(({ s, a }) => (
          <div key={a.ce.index} className="cecard saved">
            <span className="cehead"><b>#{a.ce.index + 1}</b><span className="muted">it {a.ce.iteration} · {a.ce.strategy ?? "—"}</span></span>
            {!a.shown ? <span className="muted">{tooLarge(model?.input_dim ?? 0)}</span> : shape ? (
              <span className="pixrow">
                <Pixels xs={a.seed} shape={shape} lo={lo} hi={hi} label="seed" />
                <Pixels xs={a.x} shape={shape} lo={lo} hi={hi} label="mutated" />
                <Pixels xs={a.delta} shape={shape} lo={-a.linf} hi={a.linf} mode="signed" label="δ" />
              </span>
            ) : <DeltaBars delta={a.delta} box={box} />}
            <span className="ceclass">
              {a.ce.true_class !== null
                ? <><b>{classLabel(ds, a.ce.true_class)}</b> → <b className={a.misclassified ? "state bad" : ""}>{classLabel(ds, a.pred)}</b></>
                : <>{a.ce.kind} · row {a.ce.spec_row}</>}
            </span>
            <span className="cemeta mono muted"><span>‖δ‖∞ {fmt(a.linf, 3)}</span><span>saved {new Date(s.saved_at).toLocaleString()}</span></span>
            <span className="ceactions">
              <a className="button secondary small" href={savedCounterexampleUrl(runId, a.ce.index)} download
                title="VNN-COMP result: sat + VNN-LIB 2.0 command-line assignment of X (input) and Y (output), float64">Export counterexample (VNN-LIB 2.0)</a>
              {shape && <button className="secondary small" onClick={() => png(a)}
                title={`${shape.w}×${shape.h} PNG of the mutated input at native resolution`}>Export image (.png)</button>}
            </span>
          </div>
        ))}
      </div>
      {err && <div className="error">{err}</div>}
    </>
  );
}

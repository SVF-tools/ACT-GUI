import { useEffect, useState } from "react";
import { fmt, num, tooLarge } from "../shared/wire";
import type { FuzzFrameOut, ModelDescriptionOut } from "../generated/wire";
import { Pixels } from "../shared/ui/pixels";
import { modelShape, inputBox, finiteRange } from "./presentation";
import { DeltaBars } from "./DeltaBars";
import { SaveButton } from "./SaveButton";

const PLAY_MS = 700;

// The mutated input beside the progress chart: the latest frame while running, a playable filmstrip afterwards.
export function FuzzMutations({ frames, live, model, sel, onSel, saved, onSave }: {
  frames: FuzzFrameOut[]; live: boolean; model: ModelDescriptionOut | null; sel: number | null; onSel: (i: number | null) => void;
  saved: Set<number>; onSave: (index: number) => Promise<void>;
}) {
  const [playing, setPlaying] = useState(false);
  const n = frames.length;
  const idx = Math.min(sel ?? n - 1, n - 1);
  useEffect(() => {
    if (!playing || n < 2) return;
    const t = setInterval(() => onSel((idx + 1) % n), PLAY_MS);
    return () => clearInterval(t);
  }, [playing, idx, n, onSel]);
  useEffect(() => { if (live) setPlaying(false); }, [live]);

  const fr = frames[idx];
  if (!fr) {
    return (
      <div className="mutpanel">
        <div className="note">{live ? "Waiting for the first mutated input…" : "No mutated-input frames in this record (written before they were captured). Re-run to see them."}</div>
      </div>
    );
  }
  if (!fr.input || !fr.seed_input) {
    return (
      <div className="mutpanel">
        <div className="muthead">
          <b>Mutated input</b>
          {live ? <span className="chip s-running">live · latest</span> : <span className="muted">frame {idx + 1} / {n}</span>}
          {fr.violation && <span className="chip bad">counterexample</span>}
        </div>
        <div className="note">{tooLarge(model?.input_dim ?? 0)}. Iteration {fr.iteration} · {fr.strategy ?? "—"} · depth {fr.depth}.</div>
      </div>
    );
  }
  const x = fr.input.map(num), seed = fr.seed_input.map(num);
  const delta = x.map((v, i) => v - seed[i]!);
  const linf = delta.reduce((m, d) => Math.max(m, Math.abs(d)), 0);
  const d = x.length, shape = modelShape(model, d), box = inputBox(model, d);
  const [lo, hi] = box ? finiteRange([...box.lb, ...box.ub]) : finiteRange([...x, ...seed]);
  return (
    <div className="mutpanel">
      <div className="muthead">
        <b>Mutated input</b>
        {live ? <span className="chip s-running">live · latest</span> : <span className="muted">frame {idx + 1} / {n}</span>}
        {fr.violation && <span className="chip bad">counterexample</span>}
        {fr.counterexample && <SaveButton index={fr.counterexample.index} saved={saved.has(fr.counterexample.index)} onSave={onSave} />}
      </div>
      {shape ? (
        <div className="mutimgs">
          <Pixels xs={x} shape={shape} lo={lo} hi={hi} label="mutated" size="big" />
          <div className="mutside">
            <Pixels xs={seed} shape={shape} lo={lo} hi={hi} label={`seed row ${fr.seed_row}`} />
            <Pixels xs={delta} shape={shape} lo={-linf} hi={linf} mode="signed" label="δ (red +, blue −)" />
          </div>
        </div>
      ) : <DeltaBars delta={delta} box={box} />}
      <div className="mutmeta mono muted">
        <span>it {fr.iteration} · {fmt(fr.elapsed_s, 2)} s</span>
        <span>{fr.strategy ?? "—"} · depth {fr.depth}</span>
        <span>‖δ‖∞ {fmt(linf, 4)}</span>
      </div>
      {!live && n > 1 && (
        <div className="mutctl">
          <button className="secondary" onClick={() => setPlaying(!playing)}>{playing ? "Pause" : "Play"}</button>
          <input type="range" min={0} max={n - 1} value={idx} aria-label="mutated input frame"
            onChange={(e) => { setPlaying(false); onSel(Number(e.target.value)); }} />
        </div>
      )}
      <div className="note">Lane 0 of the batch ACT mutated, sampled with the progress reports; δ is relative to its INPUT row.</div>
    </div>
  );
}

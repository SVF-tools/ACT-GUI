// The dataset metadata behind an input row's VNN-LIB property: its source sentence, replayed perturbations
// and how the box was matched to the sentence.
import type { InputProvenanceOut } from "../generated/wire";
import { wordDiff } from "./textDiff";

const MATCH = {
  verified: { cls: "good", title: "The benchmark generator's own bookkeeping, replayed by the workbench, fixes this sentence." },
  aligned: { cls: "warn", title: "Matched by order-preserving alignment of reconstructed embeddings; likely, not proven." },
  unmatched: { cls: "bad", title: "No clear source sentence was found for this box." },
} as const;

export function TextProvenance({ p }: { p: InputProvenanceOut }) {
  const m = MATCH[p.match_status];
  return (
    <div className="provenance">
      <div className="label">
        {p.task.dataset_url ? <a href={p.task.dataset_url} target="_blank" rel="noreferrer">{p.task.title}</a> : p.task.title}
        {" · "}{p.family_title} box {p.family_index}{" "}
        <span className={`chip ${m.cls}`} title={m.title}>{p.match_status}</span>
      </div>
      {p.text !== null
        ? <div className="sentence big">{p.text}</div>
        : <div className="note">No source sentence is shown: {p.match_detail}</div>}
      <div className="classrow" aria-label="output classes">
        {p.task.class_names.map((c, k) => (
          <span key={k} className={k === p.label ? "chip good" : "chip"}
            title={k === p.label ? "dataset label of the source sentence" : undefined}>{k} · {c}</span>
        ))}
      </div>
      {p.text !== null && <Variants p={p} />}
      <details>
        <summary className="note">How this box was matched</summary>
        <p className="note">{p.match_detail}.</p>
        <p className="note">Model input: {p.representation}.</p>
        <ul className="note">
          {p.sources.map((s, i) => (
            <li key={i}>{s.name}{s.commit ? ` @ ${s.commit.slice(0, 12)}` : ""}{s.revision ? ` @ ${s.revision.slice(0, 12)}` : ""}</li>
          ))}
        </ul>
      </details>
    </div>
  );
}

function Variants({ p }: { p: InputProvenanceOut }) {
  if (p.variants_status === "not_published") {
    return <div className="note">The Vicuna paraphrases that span this box were generated through an API and never published;
      only the source sentence is known.</div>;
  }
  if (p.variants_status === "not_reproduced") {
    return <div className="note">The perturbed sentences of this box could not be replayed.</div>;
  }
  return (
    <>
      <ul className="variants" aria-label="perturbed sentences">
        {p.variants.map((v, i) => (
          <li key={i} className={v.kept ? undefined : "filtered"}
            title={v.kept ? "kept by the generator's similarity filter: its point spans the box"
              : "dropped by the generator's similarity filter (cosine to the sentence at most 0.6)"}>
            <span className="kind">{v.kind.replace(/^(char|word)_/, "").replaceAll("_", " ")}</span>
            <span>{wordDiff(p.text!, v.text).map((d, j) => (
              <span key={j} className={d.op === "same" ? undefined : `diff-${d.op}`}>{d.text} </span>))}</span>
            <span className="muted mono">{v.kept ? "kept" : "filtered"}{v.cosine !== null ? ` · cos ${v.cosine.toFixed(2)}` : ""}</span>
          </li>
        ))}
      </ul>
      {p.variants_status === "partial" && <div className="note">Some perturbations of this sentence could not be replayed (see below).</div>}
    </>
  );
}

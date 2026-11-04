import { useState } from "react";
import type { ExplainResponse } from "../generated/wire";
import { useProviders, useExplain } from "./hooks";

export function AssistantView({ sel, onNavigate }: { sel: { modelId: string | null; runId: string | null; layerId: number | null; neuron: number | null }; onNavigate: (layerId: number, neuron: number | null) => void }) {
  const providers = useProviders();
  const explain = useExplain();
  const [question, setQuestion] = useState("Why is this layer's bound loose, and what decided the verdict?");
  const [answer, setAnswer] = useState<ExplainResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    if (!sel.modelId) return;
    setBusy(true);
    setErr(null);
    try {
      // The context is frozen at request time; later selection changes do not alter this answer.
      setAnswer(await explain.mutateAsync({ context: { model_id: sel.modelId, run_id: sel.runId, layer_id: sel.layerId, neuron: sel.neuron }, question }));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="assistant">
      <div className="note">
        Providers: {providers.status === "success" ? providers.data.providers.map((p) => `${p.name} (${p.kind}, ${p.availability})`).join(" · ") : "…"}
      </div>
      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3} aria-label="question" />
      <button className="primary" onClick={ask} disabled={busy || !sel.modelId || !question.trim()}>
        {busy ? "Collecting evidence…" : "Ask about current selection"}
      </button>
      {!sel.modelId && <div className="note">Select a model (and ideally a run and layer) first.</div>}
      {err && <div className="error">{err}</div>}
      {answer && (
        <div className="answer">
          <div className="note">Answer {answer.answer_id} · {answer.provider} ({answer.provider_kind}) · context frozen at run {answer.context.run_id ?? "—"}, layer {answer.context.layer_id ?? "—"}, index {answer.context.neuron ?? "—"}</div>
          {answer.sections.map((s, i) => (
            <div key={i} className={`section sec-${s.kind}`}>
              <span className="seckind">{s.kind}</span>
              <p>{s.text}</p>
              <div className="chips">
                {s.evidence.map((id) => {
                  const ev = answer.evidence.find((e) => e.ref_id === id)!;
                  return (
                    <button key={id} className="chip link" title={ev.value} disabled={ev.layer_id === null}
                      onClick={() => ev.layer_id !== null && onNavigate(ev.layer_id, ev.neuron)}>
                      {id}: {ev.label}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

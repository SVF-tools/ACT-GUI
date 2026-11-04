"""Evidence-based explanation for a selected layer/neuron of a completed run (AI-01, AI-02 partial).

Flow: freeze the SelectionContext -> collect typed evidence through the same
module services the GUI routes use -> a provider composes sections that cite
evidence ids -> every cited id must resolve to collected evidence.

Only the deterministic FakeProvider ships in this first version. It restates
ACT data and labels every derived statement; it never changes ACT's verdict.
"""
from __future__ import annotations

import math
import os
import uuid
from typing import TYPE_CHECKING, Protocol

from visual_bench.assistant import schemas as S
from visual_bench.errors import AppError
from visual_bench.wire import WireNumber

if TYPE_CHECKING:
    from visual_bench.workbench import Workbench


def _num(x: WireNumber) -> float:
    return float(x) if not isinstance(x, str) else float(x.replace("Infinity", "inf"))


class Provider(Protocol):
    name: str
    kind: str

    def compose(self, question: str, ctx: S.SelectionContext, ev: dict[str, S.EvidenceRef],
                facts: dict[str, object]) -> list[S.AnswerSection]: ...


def collect_evidence(wb: "Workbench", ctx: S.SelectionContext) -> tuple[dict[str, S.EvidenceRef], dict[str, object]]:
    ev: dict[str, S.EvidenceRef] = {}
    facts: dict[str, object] = {}

    def add(kind: S.EvidenceKind, label: str, value: str, layer_id: int | None = None, neuron: int | None = None) -> str:
        ref_id = f"ev{len(ev) + 1}"
        ev[ref_id] = S.EvidenceRef(ref_id=ref_id, kind=kind, label=label, run_id=ctx.run_id, layer_id=layer_id,
                                   neuron=neuron, value=value)
        return ref_id

    desc = wb.models.describe(ctx.model_id)
    if desc.output_spec:
        facts["spec"] = add("spec", "Output property (ASSERT layer)", desc.output_spec.text, desc.output_spec.layer_id)
    if not ctx.run_id:
        return ev, facts
    run = wb.runs.get(ctx.run_id)
    if run.model_id != ctx.model_id:
        raise AppError(422, "context_mismatch", "run_id belongs to a different model than the selection")
    if run.result:
        facts["verdict"] = run.result.verdict
        facts["method"] = run.method
        facts["result"] = add("run_result", f"ACT verdict ({run.method})",
                              f"{run.result.act_status} in {run.result.elapsed_s:.3f}s")
    else:
        facts["run_status"] = run.status
    cov = wb.bab.coverage(ctx.run_id)
    facts["coverage"] = add("coverage", "BaB observation coverage",
                            f"node events {cov.node_events}; final summary {cov.final_summary}; {cov.reason}")
    if cov.summary:
        facts["bab_nodes"] = cov.summary.get("nodes")
    states = wb.analysis.layer_states(ctx.run_id)
    facts["layers_availability"] = states.availability
    if ctx.layer_id is None or states.availability != "available":
        return ev, facts
    by_id = {l.layer_id: l for l in states.layers}
    layer = by_id.get(ctx.layer_id)
    if layer is None:
        facts["layer_missing"] = True
        return ev, facts
    lb, ub = [_num(x) for x in layer.lb], [_num(x) for x in layer.ub]
    widths = [u - l for l, u in zip(lb, ub)]
    widest = max(range(len(widths)), key=lambda i: widths[i]) if widths else None
    facts["layer"] = add("layer_state", f"Layer {layer.layer_id} ({layer.kind}) interval bounds after the layer",
                         f"{len(lb)} values; mean width {sum(widths) / max(len(widths), 1):.4g}; "
                         f"widest index {widest} width {widths[widest] if widest is not None else float('nan'):.4g}",
                         layer.layer_id)
    facts["layer_kind"] = layer.kind
    if layer.kind == "RELU" and layer.before_layer_ids:
        pre = by_id.get(layer.before_layer_ids[0])
        if pre:
            plb, pub = [_num(x) for x in pre.lb], [_num(x) for x in pre.ub]
            unstable = [i for i, (l, u) in enumerate(zip(plb, pub)) if l < 0 < u]
            facts["unstable"] = add("layer_state", f"Pre-activation bounds (layer {pre.layer_id})",
                                    f"{len(unstable)} of {len(plb)} ReLU inputs cross zero (indices {unstable[:12]})",
                                    pre.layer_id)
            facts["unstable_count"] = len(unstable)
    if ctx.neuron is not None:
        if ctx.neuron >= len(lb):
            facts["neuron_missing"] = True
        else:
            i = ctx.neuron
            facts["neuron"] = add("layer_state", f"Layer {layer.layer_id} value {i}",
                                  f"[{lb[i]:.6g}, {ub[i]:.6g}] (width {widths[i]:.4g})", layer.layer_id, i)
    if desc.output_spec and desc.output_spec.matrix and desc.output_spec.thresholds and \
            desc.output_spec.layer_id in by_id and by_id[desc.output_spec.layer_id].before_layer_ids:
        out_layer = by_id.get(by_id[desc.output_spec.layer_id].before_layer_ids[0])
        if out_layer:
            olb, oub = [_num(x) for x in out_layer.lb], [_num(x) for x in out_layer.ub]
            row, thr = desc.output_spec.matrix[0], _num(desc.output_spec.thresholds[0])
            upper = sum(max(c * l, c * u) for c, l, u in zip(row, olb, oub))
            if math.isfinite(upper):
                facts["margin"] = add("layer_state", "Interval upper bound of C@y (row 0) vs threshold",
                                      f"{upper:.6g} vs threshold {thr:.6g}", out_layer.layer_id)
                facts["margin_ok"] = upper <= thr
    return ev, facts


class FakeProvider:
    """Deterministic template provider for development and tests (not a language model)."""

    name = "fake-deterministic"
    kind = "fake"

    def compose(self, question: str, ctx: S.SelectionContext, ev: dict[str, S.EvidenceRef],
                facts: dict[str, object]) -> list[S.AnswerSection]:
        out: list[S.AnswerSection] = []

        def sec(kind: str, text: str, *keys: str) -> None:
            refs = [str(facts[k]) for k in keys if k in facts]
            out.append(S.AnswerSection(kind=kind, text=text, evidence=refs))  # type: ignore[arg-type]

        if "result" in facts:
            sec("observation", f"ACT reported {str(facts['verdict']).upper()} for this run ({facts['method']}). "
                "This verdict comes from ACT and is not re-derived here.", "result")
        elif "run_status" in facts:
            sec("missing", f"The run is {facts['run_status']}; there is no ACT verdict to cite yet.")
        else:
            sec("missing", "No run is selected, so only the specification can be cited. Start a run to inspect bounds.", "spec")
        if "layer" in facts:
            sec("observation", f"Selected layer evidence: {ev[str(facts['layer'])].value}.", "layer")
        elif ctx.layer_id is not None:
            sec("missing", f"Layer {ctx.layer_id} has no recorded state (availability: {facts.get('layers_availability')}).")
        if "neuron" in facts:
            sec("observation", f"Selected value: {ev[str(facts['neuron'])].value}.", "neuron")
        elif facts.get("neuron_missing"):
            sec("missing", f"Index {ctx.neuron} is outside the selected layer.")
        if "unstable" in facts:
            n = facts.get("unstable_count", 0)
            sec("interpretation", f"{n} ReLU input(s) cross zero, so interval analysis must over-approximate them; "
                "these are the natural split candidates for BaB." if n else
                "No ReLU input crosses zero here, so this layer adds no ReLU relaxation error.", "unstable")
        if "margin" in facts:
            ok = facts.get("margin_ok")
            sec("interpretation", "The interval upper bound of the property already meets the threshold, consistent "
                "with interval certification." if ok else
                "The interval upper bound exceeds the threshold, so interval analysis alone is inconclusive here; "
                "refinement (BaB) is needed to decide the property.", "margin", "spec")
            if not ok and facts.get("verdict") == "certified" and facts.get("method") == "bab":
                sec("hypothesis", f"BaB closed the gap by splitting ({facts.get('bab_nodes')} node(s) per ACT's summary); "
                    "which splits were made is not observable in this ACT baseline.", "coverage", "result")
        sec("missing" if "coverage" in facts else "observation",
            "Node-level BaB history is unsupported by the pinned ACT baseline; only the final summary is shown.",
            "coverage")
        return out


def providers() -> S.ProviderList:
    real_note = "No real provider is wired in this first version; set up AI-02 provider integration."
    return S.ProviderList(providers=[
        S.ProviderOut(name=FakeProvider.name, kind="fake", availability="available",
                      note="Deterministic templates over ACT evidence; not a language model."),
        S.ProviderOut(name="anthropic", kind="real",
                      availability="not_configured", note=real_note if not os.environ.get("ANTHROPIC_API_KEY") else
                      "ANTHROPIC_API_KEY is set, but the adapter is not implemented yet."),
    ])


def explain(wb: "Workbench", req: S.ExplainRequest, provider: Provider | None = None) -> S.ExplainResponse:
    ctx = req.context.model_copy(deep=True)  # frozen for the whole request
    ev, facts = collect_evidence(wb, ctx)
    p = provider or FakeProvider()
    sections = p.compose(req.question, ctx, ev, facts)
    for s in sections:
        for ref in s.evidence:
            if ref not in ev:
                raise AppError(500, "unresolved_evidence", f"Provider cited unknown evidence {ref!r}")
    return S.ExplainResponse(answer_id="ans-" + uuid.uuid4().hex[:10], provider=p.name, provider_kind=p.kind,  # type: ignore[arg-type]
                             context=ctx, question=req.question, sections=sections, evidence=list(ev.values()))

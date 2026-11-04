"""Assistant context, evidence, and explanation payloads (/api/assistant/*)."""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from visual_bench.wire import Wire

__all__ = ['SelectionContext', 'ExplainRequest', 'EvidenceKind', 'EvidenceRef', 'AnswerSection', 'ExplainResponse', 'ProviderOut', 'ProviderList']


class SelectionContext(Wire):
    model_id: str
    run_id: str | None = None
    layer_id: int | None = None
    neuron: int | None = Field(default=None, ge=0)

class ExplainRequest(Wire):
    context: SelectionContext
    question: str = Field(min_length=1, max_length=2000)

EvidenceKind = Literal["layer_state", "run_result", "spec", "coverage"]

class EvidenceRef(Wire):
    ref_id: str
    kind: EvidenceKind
    label: str
    run_id: str | None
    layer_id: int | None
    neuron: int | None
    value: str

class AnswerSection(Wire):
    kind: Literal["observation", "interpretation", "hypothesis", "missing"]
    text: str
    evidence: list[str]

class ExplainResponse(Wire):
    answer_id: str
    provider: str
    provider_kind: Literal["fake", "real"]
    context: SelectionContext
    question: str
    sections: list[AnswerSection]
    evidence: list[EvidenceRef]

class ProviderOut(Wire):
    name: str
    kind: Literal["fake", "real"]
    availability: Literal["available", "not_configured"]
    note: str

class ProviderList(Wire):
    providers: list[ProviderOut]

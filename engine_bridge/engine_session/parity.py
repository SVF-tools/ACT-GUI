"""ACT API parity checks (ES-06): does this checkout expose every ACT symbol the bridge adapters call?

Each capability lists the ACT functions/classes its adapter imports, with the keyword parameters and
number of positional arguments the adapter passes. A capability is advertised only when all of its
requirements resolve on the imported checkout. This checks the interface, not numerical semantics:
native parity tests against recorded results remain the evidence for a pinned baseline.
"""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, cast

from engine_bridge.contracts import ApiCheck


@dataclass(frozen=True)
class Requirement:
    symbol: str  # "package.module:Attr" or "package.module:Class.attr"
    params: tuple[str, ...] = ()  # parameter names passed by keyword
    positional: int = 0  # arguments passed positionally (including self for methods read off a class)


_FUZZ_CONFIG = ("max_iterations", "timeout_seconds", "stop_on_first_violation", "save_counterexamples",
                "output_dir", "report_interval", "verbose", "trace_level")
_SERIALIZATION = "act.back_end.serialization.serialization"
_VERIFIER = "act.back_end.verifier"
_TF = "act.back_end.transfer_functions"
_WRAP = (
    Requirement(f"{_SERIALIZATION}:save_net_to_file", positional=2),
    Requirement("act.front_end.model_synthesis:infer_layout_from_tensor", positional=1),
    Requirement("act.front_end.spec_creator_base:LabeledInputTensor", positional=2),
    Requirement("act.front_end.verifiable_model:VerifiableModel", ("input_layer", "input_spec", "output_spec")),
    Requirement("act.front_end.verifiable_model:InputLayer", ("layout", "dataset_name"), positional=3),
    Requirement("act.front_end.verifiable_model:InputSpecLayer", ("spec",)),
    Requirement("act.front_end.verifiable_model:OutputSpecLayer", ("spec",)),
    Requirement("act.pipeline.verification.torch2act:TorchToACT", ("sample_input",), positional=1),
    Requirement("act.util.device_manager:get_default_device"),
    Requirement("act.util.device_manager:get_default_dtype"),
)
_VERIFY_ONCE = (
    Requirement(f"{_SERIALIZATION}:load_net_from_file", positional=1),
    Requirement(f"{_VERIFIER}:verify_once", positional=1),
    Requirement(f"{_TF}:set_solver_mode", positional=1),
    Requirement(f"{_TF}:set_transfer_function_mode", positional=1),
)


def requirements() -> dict[str, tuple[Requirement, ...]]:
    from engine_bridge.execution.fuzz import TUNABLE  # lazy: execution imports engine_session

    bab = (
        Requirement(f"{_SERIALIZATION}:load_net_from_file", positional=1),
        Requirement("act.back_end.bab.bab:verify_bab_batched",
                    ("net", "solver_factory", "config", "max_batch_size", "time_budget_s", "dual_config")),
        Requirement("act.back_end.solver.solver_torchlp:TorchLPSolver"),
        Requirement("act.config.config:PipelineConfig.from_yaml"),
        Requirement("act.config.config:BackendConfig", ("bab_max_batch_size",)),
        Requirement("act.config.config:BackendConfig.from_yaml"),
    )
    return {
        "model.load_json": (Requirement(f"{_SERIALIZATION}:load_net_from_file", positional=1),),
        "spec.read": (Requirement(f"{_VERIFIER}:get_input_ids", positional=1),
                      Requirement(f"{_VERIFIER}:get_output_ids", positional=1)),
        "verify.interval": _VERIFY_ONCE,
        "verify.dual": _VERIFY_ONCE,
        "verify.dual.options": (
            *_VERIFY_ONCE,
            Requirement(f"{_VERIFIER}:verify_once", ("dual_iters", "dual_config", "dual_refresh_forward"), positional=1),
            Requirement("act.config.config:DualConfig", ("n_iters", "lr_alpha", "lr_decay", "per_class_alpha",
                                                          "stagnation_patience", "stagnation_tol", "max_time",
                                                          "forward_lin_max_perturbed")),
        ),
        "observe.propagation": (
            *_VERIFY_ONCE,
            Requirement("act.pipeline.gui.observe:observe", positional=1),
            Requirement("act.pipeline.gui.observe:emit", positional=1),
            *(Requirement(f"act.pipeline.gui.observe:{name}") for name in
              ("RecordKey", "LayerBounds", "Relaxation", "DualBackward", "SpecBound")),
        ),
        "verify.hybridz": (
            *_VERIFY_ONCE,
            Requirement(f"{_VERIFIER}:verify_once", ("timelimit", "hybridz_tolerance"), positional=1),
            Requirement(f"{_TF}:set_transfer_function_mode", positional=2),
            Requirement("act.config.config:BackendConfig", ("hybridz",)),
            Requirement("act.config.config:BackendConfig.from_yaml"),
        ),
        "verify.bab": bab,
        "events.bab_summary": bab,
        "fuzz.actfuzzer": (
            Requirement(f"{_SERIALIZATION}:load_net_from_file", positional=1),
            Requirement("act.pipeline.fuzzing.actfuzzer:ACTFuzzer", ("wrapped_model", "initial_seeds", "config")),
            Requirement("act.pipeline.fuzzing.actfuzzer:ACTFuzzer._print_progress", positional=2),
            Requirement("act.pipeline.fuzzing.actfuzzer:FuzzingConfig", (*_FUZZ_CONFIG, *sorted(TUNABLE))),
            Requirement("act.pipeline.fuzzing.actfuzzer:FuzzingConfig.from_yaml", _FUZZ_CONFIG),
            Requirement("act.pipeline.fuzzing.mutations:MutationEngine.mutate", positional=2),
            Requirement("act.pipeline.verification.act2torch:ACTToTorch.run", positional=1),
            Requirement("act.front_end.verifiable_model:VerifiableModel.set_strict_mode", positional=1),
            Requirement("act.front_end.verifiable_model:VerifiableModel.get_strict_mode"),
            Requirement("act.front_end.spec_creator_base:LabeledInputTensor", ("tensor", "label")),
            Requirement("act.config.config:read_fuzzing_section", positional=1),
        ),
        "inspect.layer_bounds.interval": (
            Requirement("act.back_end.analyze:analyze", positional=3),
            Requirement("act.back_end.core:Fact", ("bounds", "cons")),
            Requirement("act.back_end.core:ConSet"),
            Requirement(f"{_TF}:set_solver_mode", positional=1),
            Requirement(f"{_TF}:set_transfer_function_mode", positional=1),
            Requirement(f"{_VERIFIER}:_setup_verify_context", positional=1),
            Requirement(f"{_VERIFIER}:add_all_input_specs", positional=3),
            Requirement(f"{_VERIFIER}:find_entry_layer_id", positional=1),
            Requirement(f"{_VERIFIER}:get_input_ids", positional=1),
        ),
        "source.vnnlib": (
            Requirement("act.front_end.vnnlib_loader.create_specs:create_specs_from_paths", ("category",), positional=2),
            *_WRAP,
        ),
        "source.onnx_classifier": (
            Requirement("act.front_end.vnnlib_loader.onnx_converter:convert_onnx_to_pytorch", ("simplify",), positional=1),
            Requirement("act.front_end.vnnlib_loader.onnx_converter:get_onnx_input_shape", positional=1),
            Requirement("act.front_end.specs:InKind"),
            Requirement("act.front_end.specs:InputSpec"),
            Requirement("act.front_end.specs:OutKind"),
            Requirement("act.front_end.specs:OutputSpec"),
            *_WRAP,
        ),
    }


def _check(req: Requirement) -> str | None:
    """None when the requirement holds, else what is missing."""
    module, _, path = req.symbol.partition(":")
    try:
        obj: Any = importlib.import_module(module)
    except Exception as exc:  # a broken submodule makes the capability unavailable, not the probe
        return f"cannot import {module}: {exc}"
    for part in path.split("."):
        if not hasattr(obj, part):
            return f"{module} has no {path}"
        obj = getattr(obj, part)
    if not (req.params or req.positional):
        return None
    try:
        params = list(inspect.signature(cast(Any, obj)).parameters.values())
    except (TypeError, ValueError):
        return f"{req.symbol} has no inspectable signature"
    kinds = {p.kind for p in params}
    if inspect.Parameter.VAR_KEYWORD not in kinds:
        names = {p.name for p in params if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}
        missing = [n for n in req.params if n not in names]
        if missing:
            return f"{req.symbol} does not accept {', '.join(missing)}"
    if inspect.Parameter.VAR_POSITIONAL not in kinds:
        slots = sum(p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) for p in params)
        if slots < req.positional:
            return f"{req.symbol} takes {slots} positional arguments, the bridge passes {req.positional}"
    return None


def check_api() -> tuple[ApiCheck, ...]:
    """Run inside act_imports(): one ApiCheck per (capability, requirement)."""
    out = []
    for capability, reqs in requirements().items():
        for req in reqs:
            problem = _check(req)
            out.append(ApiCheck(capability, req.symbol, problem is None, problem or "ok"))
    return tuple(out)

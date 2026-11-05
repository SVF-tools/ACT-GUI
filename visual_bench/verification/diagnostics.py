"""Run diagnostics: what the GUI saw while driving ACT, and the reproduction snapshot built from it.

Worker side (`Capture`): Python warnings, WARNING+ log records, and the full exception chain of a failed
ACT call, with each traceback frame attributed to ACT, engine_bridge, visual_bench, or a library, and the
error location taken from the innermost ACT frame.
Service side (`snapshot_zip`): one zip holding the run's parameters, the ACT net it ran (its INPUT_SPEC
and ASSERT are the instance), the engine it ran on, the captured logs and diagnostics, and reproduce.py.

Absolute server paths are replaced by placeholders (<ACT>, <ACT-GUI>, ...) before anything is stored.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import traceback
import warnings
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any

MAX_ENTRIES = 200  # warnings and log records kept per run; the rest are counted
MAX_TEXT = 4000  # characters kept per message
LOG_TAIL_BYTES = 1 << 20  # bytes kept of each worker log (the tail, where failures are)
DIAGNOSTICS_VERSION = 1
SUMMARY_MESSAGES = 5
# ACT reports many problems with print("[WARN] ...") rather than the warnings module.
_PRINTED = re.compile(r"^\s*(?:\[(WARN|WARNING|ERROR|ERR)\]|(WARNING|Warning|ERROR|Error):)\s*(.*)$")

Scrub = Callable[[str], str]


def scrubber(roots: dict[str, Path | str | None]) -> Scrub:
    """Replace absolute root paths by their placeholders, longest path first, at path-component boundaries only."""
    pairs = sorted(((str(Path(p).resolve()) if p else "", name) for name, p in roots.items()), key=lambda x: -len(x[0]))
    patterns = [(re.compile(rf"(?<![\w.-]){re.escape(p)}(?![\w.-])"), n) for p, n in pairs if len(p) > 1]

    def scrub(text: str) -> str:
        for pattern, name in patterns:
            text = pattern.sub(lambda _: name, text)
        return text

    return scrub


def default_roots(extra: dict[str, Path | str | None] | None = None) -> dict[str, Path | str | None]:
    from engine_bridge.engine_session import act_code_root, act_root
    from visual_bench.config import REPO_ROOT

    return {"<ACT>": act_code_root(), "<ACT_ROOT>": act_root(), "<ACT-GUI>": REPO_ROOT,
            "<python>": sys.prefix, "<python-base>": sys.base_prefix, "~": Path.home(), **(extra or {})}


def origin(scrubbed_file: str) -> str:
    """Which code a (scrubbed) frame belongs to."""
    if scrubbed_file.startswith(("<ACT>/", "<ACT_ROOT>/")):
        return "act"
    for part in ("engine_bridge", "visual_bench"):
        if scrubbed_file.startswith(f"<ACT-GUI>/{part}/"):
            return part
    return "library"


def _clip(text: str) -> str:
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + f"... [{len(text) - MAX_TEXT} characters cut]"


def describe_exception(exc: BaseException, scrub: Scrub) -> dict[str, Any]:
    """The exception chain (outermost first) with attributed frames, and the error location."""
    chain: list[BaseException] = []
    e: BaseException | None = exc
    while e is not None and all(e is not c for c in chain):
        chain.append(e)
        e = e.__cause__ if e.__cause__ is not None else None if e.__suppress_context__ else e.__context__
    entries = []
    for x in chain:
        frames = []
        for f in traceback.extract_tb(x.__traceback__):
            file = scrub(f.filename)
            frames.append({"file": file, "line": f.lineno, "function": f.name, "origin": origin(file),
                           "code": f.line or ""})
        entries.append({"type": f"{type(x).__module__}.{type(x).__qualname__}", "message": _clip(scrub(str(x))),
                        "code": getattr(x, "code", None), "frames": frames})
    location = None
    for entry in reversed(entries):  # the root cause first, then the exceptions wrapping it
        act = [f for f in entry["frames"] if f["origin"] == "act"]
        if act or entry["frames"]:
            location = (act or entry["frames"])[-1]
            break
    return {"exception": f"{entries[-1]['type']}: {entries[-1]['message']}".split("\n")[0][:300],
            "location": location, "chain": entries,
            "traceback": _clip(scrub("".join(traceback.format_exception(exc))))}


def location_text(loc: dict[str, Any] | None) -> str | None:
    return None if loc is None else f"{loc['file']}:{loc['line']} in {loc['function']}"


class _Records(logging.Handler):
    def __init__(self, capture: Capture) -> None:
        super().__init__(logging.WARNING)
        self.capture = capture

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
        except Exception as exc:  # a malformed log call must not end the run; keep what it was
            message = f"{record.msg!r} (unformattable: {exc!r})"
        self.capture.add("logs", {"level": record.levelname, "logger": record.name,
                                  "file": self.capture.scrub(record.pathname), "line": record.lineno,
                                  "message": _clip(self.capture.scrub(message))})


class Capture:
    """Collect warnings, WARNING+ log records, notes, and the failing exception inside the run worker.

    Entering installs a warnings recorder and a root log handler and silences log levels below WARNING
    (ACT's INFO chatter); leaving restores the previous state.
    """

    def __init__(self, scrub: Scrub) -> None:
        self.scrub = scrub
        self.entries: dict[str, list[dict[str, Any]]] = {"warnings": [], "logs": [], "notes": []}
        self.dropped = {"warnings": 0, "logs": 0, "notes": 0}
        self.error: dict[str, Any] | None = None
        self._handler = _Records(self)
        self._warnings = warnings.catch_warnings()
        self._disabled = logging.NOTSET

    def add(self, kind: str, entry: dict[str, Any]) -> None:
        if len(self.entries[kind]) < MAX_ENTRIES:
            self.entries[kind].append(entry)
        else:
            self.dropped[kind] += 1

    def _warning(self, message: Warning | str, category: type[Warning], filename: str, lineno: int,
                 file: Any = None, line: str | None = None) -> None:
        file_ = self.scrub(filename)
        self.add("warnings", {"category": category.__name__, "message": _clip(self.scrub(str(message))),
                              "file": file_, "line": lineno, "origin": origin(file_)})

    def __enter__(self) -> Capture:
        self._warnings.__enter__()
        warnings.simplefilter("default")  # once per location; ACT's own filters, set at import, still win
        warnings.showwarning = self._warning
        self._disabled = logging.root.manager.disable
        logging.disable(logging.INFO)
        logging.getLogger().addHandler(self._handler)
        return self

    def __exit__(self, et: type[BaseException] | None, ev: BaseException | None, tb: TracebackType | None) -> None:
        logging.getLogger().removeHandler(self._handler)
        logging.disable(self._disabled)
        self._warnings.__exit__(et, ev, tb)

    def note(self, code: str, message: str) -> None:
        """A non-fatal problem the worker handled (e.g. layer states not recorded)."""
        self.add("notes", {"code": code, "message": _clip(self.scrub(message))})

    def exception(self, exc: BaseException) -> None:
        self.error = describe_exception(exc, self.scrub)

    def report(self) -> dict[str, Any]:
        return {**self.entries, "dropped": self.dropped, "error": self.error, "runtime": runtime(self.scrub)}


def runtime(scrub: Scrub) -> dict[str, Any]:
    """The interpreter, torch and ACT modules this worker actually ran."""
    import platform

    out: dict[str, Any] = {"python": sys.version.split()[0], "platform": platform.platform(),
                           "executable": scrub(sys.executable),
                           "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    act_file = getattr(sys.modules.get("act"), "__file__", None)
    out["act_module"] = scrub(str(Path(act_file).parent)) if act_file else None
    torch = sys.modules.get("torch")
    if torch is not None:
        out["torch"] = torch.__version__
        out["cuda_available"] = bool(torch.cuda.is_available())
        out["cuda_device_count"] = torch.cuda.device_count() if out["cuda_available"] else 0
    return out


def log_tail(path: Path, scrub: Scrub) -> tuple[str, dict[str, Any]]:
    """The last LOG_TAIL_BYTES of a worker log, scrubbed, with its original size."""
    if not path.is_file():
        return "", {"bytes": 0, "truncated": False}
    size = path.stat().st_size
    with open(path, "rb") as f:
        f.seek(max(0, size - LOG_TAIL_BYTES))
        data = f.read()
    text = scrub(data.decode("utf-8", errors="replace"))
    return text, {"bytes": size, "truncated": size > LOG_TAIL_BYTES}


def printed_problems(text: str, log_name: str) -> list[dict[str, Any]]:
    """Warning and error lines ACT printed to a worker log, with their line numbers."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        m = _PRINTED.match(line)
        if m and len(out) < MAX_ENTRIES:
            level = "ERROR" if (m.group(1) or m.group(2) or "").upper().startswith("ERR") else "WARNING"
            out.append({"log": log_name, "line": n, "level": level, "message": _clip(m.group(3))})
    return out


def summary(diag: dict[str, Any]) -> dict[str, Any]:
    """The small per-run summary shown in the run history."""
    worker = diag.get("worker") or {}
    error = worker.get("error") or {}
    logs, printed = worker.get("logs", []), diag.get("printed", [])
    warned = ([f"{w['category']}: {w['message']}" for w in worker.get("warnings", [])]
              + [f"{r['logger']}: {r['message']}" for r in logs if r["level"] == "WARNING"]
              + [f"[ACT] {p['message']}" for p in printed if p["level"] == "WARNING"]
              + [f"{n['code']}: {n['message']}" for n in worker.get("notes", [])])
    errors = sum(1 for r in logs if r["level"] in ("ERROR", "CRITICAL")) + sum(
        1 for p in printed if p["level"] == "ERROR")
    return {"warnings": len(warned) + worker.get("dropped", {}).get("warnings", 0), "errors": errors,
            "messages": [m.split("\n")[0][:300] for m in warned[:SUMMARY_MESSAGES]],
            "exception": error.get("exception"), "location": location_text(error.get("location"))}


REPRODUCE_PY = '''"""Re-run this snapshot's ACT call through the same worker the workbench used.

    ACT_ROOT=/path/to/ACT python reproduce.py --act-gui /path/to/ACT-GUI

Check out ACT at the commit in diagnostics.json "engine" (for a branch run also set ACT_CODE_ROOT to a
checkout of that branch head). The worker writes its output, including the captured warnings and the
error location, to reproduced_output.json next to this file.
"""
import argparse
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--act-gui", default=os.environ.get("ACT_GUI_ROOT", "."), help="ACT-GUI checkout")
args = parser.parse_args()
sys.path.insert(0, str(Path(args.act_gui).resolve()))
from visual_bench.verification.worker import main  # noqa: E402

request = json.loads((here / "request.json").read_text())
request["model_path"] = str(here / request["model_path"])
request["record_directory"] = str(here / "reproduced_records")
with tempfile.TemporaryDirectory() as tmp:
    req_file, out_file = Path(tmp) / "request.json", Path(tmp) / "output.json"
    req_file.write_text(json.dumps(request))
    read_fd, write_fd = os.pipe()
    progress = []
    reader = threading.Thread(target=lambda: progress.extend(os.fdopen(read_fd)), daemon=True)
    reader.start()
    main(str(req_file), str(out_file), write_fd)
    reader.join()
    out = json.loads(out_file.read_text())
(here / "reproduced_output.json").write_text(json.dumps(out, indent=2))
diag = out.get("diagnostics") or {}
error = diag.get("error") or {}
print("error:", json.dumps(out["error"]) if "error" in out else None)
print("verdict:", (out.get("outcome") or {}).get("verdict"))
print("exception:", error.get("exception"))
print("location:", error.get("location"))
print("warnings:", len(diag.get("warnings", [])), "log records:", len(diag.get("logs", [])),
      "progress lines:", len(progress))
'''


def _readme(run_id: str, manifest: dict[str, Any], status: str, failure: dict[str, Any] | None,
            diag: dict[str, Any] | None, model_note: str | None, files: list[str]) -> str:
    req = manifest["request"]
    engine = (diag or {}).get("engine") or {}
    src = engine.get("source") or manifest["act"].get("source") or {}
    worker = (diag or {}).get("worker") or {}
    rt = worker.get("runtime") or {}
    s = summary(diag) if diag else None
    lines = [f"# Reproduction snapshot of {run_id}", "",
             f"- Status: {status}" + (f" ({failure['code']}: {failure['message']})" if failure else ""),
             f"- Method: {req['method']}" + (f", domain {req['domain']}" if req.get("domain") else "")
             + f", budget {req['time_budget_s']} s",
             f"- Model: {req['model_id']} (sha256 {manifest['model']['sha256']})",
             f"- ACT engine: commit {engine.get('commit', manifest['act'].get('commit'))}"
             + f", source {src.get('kind', 'baseline')}"
             + (f" {src.get('remote')}/{src.get('branch')}" if src.get("kind") == "branch" else "")
             + f", expected baseline {engine.get('expected_commit', manifest['act'].get('expected_commit'))}"
             + (", tracked changes in the checkout" if engine.get("tracked_changes") else ""),
             f"- Runtime: Python {rt.get('python', engine.get('python'))}, torch {rt.get('torch', engine.get('torch'))}"
             + f", requested device {manifest['execution'].get('requested_device')}"]
    if s:
        lines += [f"- Exception: {s['exception'] or 'none'}", f"- Error location: {s['location'] or 'none'}",
                  f"- Warnings: {s['warnings']}, log errors: {s['errors']}"]
    else:
        lines.append("- Diagnostics: not captured (the run predates diagnostics capture)")
    if model_note:
        lines.append(f"- Model file: {model_note}")
    lines += ["", "## Reproduce", "",
              "```bash", "ACT_ROOT=/path/to/ACT python reproduce.py --act-gui /path/to/ACT-GUI", "```", "",
              "`request.json` is the exact worker request; the ACT net in `model/` carries the input box and "
              "property (the instance). ACT computes every verdict; this bundle only replays the call.", "",
              "## Files", "", *[f"- `{f}`" for f in files], ""]
    return "\n".join(lines)


def snapshot_zip(run_id: str, run_dir: Path, manifest: dict[str, Any], status: str,
                 failure: dict[str, Any] | None, diag: dict[str, Any] | None,
                 model_file: Path | None, model_entry: dict[str, Any], model_note: str | None) -> bytes:
    req = manifest["request"]
    model_name = f"model/{req['model_id']}.json"
    request = (diag or {}).get("request") or {"method": req["method"], "time_budget_s": req["time_budget_s"],
                                              "domain": req.get("domain"), "fuzz": req.get("fuzz"),
                                              "record_layers": True}
    request = {**request, "model_path": model_name}
    files: dict[str, bytes] = {
        "request.json": json.dumps(request, indent=2).encode(),
        "model/entry.json": json.dumps(model_entry, indent=2, sort_keys=True).encode(),
        "reproduce.py": REPRODUCE_PY.encode(),
    }
    if model_file is not None:
        files[model_name] = model_file.read_bytes()
    for name in ("manifest.json", "events.jsonl", "result.json", "fuzzing.json", "artifacts.json",
                 "layers.json", "propagation.json",
                 *(p.relative_to(run_dir).as_posix() for p in (run_dir / "blobs").glob("*.f32"))):
        if (run_dir / name).is_file():
            files[f"run/{name}"] = (run_dir / name).read_bytes()
    for name in ("diagnostics.json", "act_stdout.log", "worker_stderr.log"):
        if (run_dir / name).is_file():
            files[name if name.endswith(".json") else f"logs/{name}"] = (run_dir / name).read_bytes()
    readme = _readme(run_id, manifest, status, failure, diag, model_note, ["README.md", *sorted(files)])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{run_id}-snapshot/README.md", readme)
        for name, data in sorted(files.items()):
            z.writestr(f"{run_id}-snapshot/{name}", data)
    return buf.getvalue()

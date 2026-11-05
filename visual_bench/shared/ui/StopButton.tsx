import { useState } from "react";
import type { RunRequest } from "../../generated/wire";
type Method = RunRequest["method"];

/** Stop a queued or running run: fuzzing ends after its current iteration and keeps what ACT found; verify/BaB are ended. */
export function StopButton({ method, onStop }: { method: Method; onStop: () => Promise<unknown> }) {
  const [state, setState] = useState<"idle" | "stopping" | "error">("idle");
  const [err, setErr] = useState("");
  async function stop() {
    setState("stopping");
    try {
      await onStop();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
      setState("error");
    }
  }
  return (
    <button className="danger" disabled={state === "stopping"} onClick={stop}
      title={err || (method === "fuzz" ? "ACTFuzzer stops after the current iteration; counterexamples found so far are kept"
        : "Ends the worker; ACT returns no result for this run")}>
      {state === "stopping" ? "Stopping…" : state === "error" ? "Stop failed, retry" : "Stop"}
    </button>
  );
}

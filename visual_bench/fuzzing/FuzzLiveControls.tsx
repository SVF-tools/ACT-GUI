import { useState } from "react";
import { StopButton } from "../shared/ui/StopButton";
import { useStopRun } from "../verification/hooks";
import type { FuzzingOut, FuzzControlStateOut } from "../generated/wire";
import { useFuzzControl, useFuzzOptions } from "./hooks";
import { FuzzOptionInput } from "./FuzzOptionInput";
import { changedLiveOptions, displayOptionValue, optionLabel, validOption, type FuzzOptionValue } from "./options";

export function FuzzLiveControls({ f }: { f: FuzzingOut }) {
  const schema = useFuzzOptions();
  const command = useFuzzControl(f.run_id);
  const stop = useStopRun();
  const [draft, setDraft] = useState<Record<string, FuzzOptionValue>>({});
  const active = f.status === "queued" || f.status === "running";
  const supported = schema.data?.live_control === true;
  const options = schema.data?.options.filter((option) => option.live) ?? [];
  const current = f.control?.live ?? {};
  const changes = changedLiveOptions(options, current, draft);
  const dirty = Object.keys(changes).length > 0;
  const valid = options.every((option) => !Object.hasOwn(changes, option.name) || validOption(option, changes[option.name]));
  const ready = supported && f.status === "running" && f.control != null;
  const history = f.control?.changes ?? [];
  const paused = f.control?.paused === true;
  if (!active && history.length === 0) return null;

  return (
    <section className="fuzzcontrols" aria-label="Fuzzing controls">
      {active && <>
        <div className="actions">
          {paused && <span className="chip">Paused</span>}
          <button type="button" className="secondary fuzzpause" disabled={!ready || command.isPending}
            onClick={() => command.mutate({ action: paused ? "resume" : "pause" })}>
            {paused ? "Resume" : "Pause"}
          </button>
          <StopButton method="fuzz" onStop={() => supported && f.status === "running"
            ? command.mutateAsync({ action: "stop" }) : stop.mutateAsync(f.run_id)} />
        </div>
        {schema.isPending ? <p className="note">Loading live controls...</p>
          : schema.isError ? <p className="note">Live controls unavailable: {schema.error.message}. Stop remains available.</p>
            : !supported ? <p className="note">This engine does not support live settings or pause. Stop remains available.</p>
              : !ready && <p className="note">Waiting for the running worker's settings.</p>}
        {supported && (
          <details className="fuzzadvanced fuzzliveoptions">
            <summary>Live settings</summary>
            <form onSubmit={(event) => {
              event.preventDefault();
              if (ready && dirty && valid && !command.isPending) {
                command.mutate({ action: "update", changes }, { onSuccess: () => setDraft({}) });
              }
            }}>
              <div className="fuzzgrid">
                {options.map((option) => (
                  <FuzzOptionInput key={option.name} option={option}
                    value={Object.hasOwn(draft, option.name) ? draft[option.name] : current[option.name]}
                    disabled={!ready || command.isPending || !Object.hasOwn(current, option.name)}
                    onChange={(value) => { command.reset(); setDraft((previous) => ({ ...previous, [option.name]: value })); }} />
                ))}
              </div>
              <div className="actions">
                <button type="submit" className="primary" disabled={!ready || !dirty || !valid || command.isPending}>Apply</button>
              </div>
              {!valid && <p className="note state bad" role="alert">Check the edited values and allowed ranges.</p>}
            </form>
          </details>
        )}
        {command.isError && <p className="error" role="alert">{command.error.message}</p>}
        {command.isSuccess && <p className="note" role="status">
          {command.data.status === "duplicate" ? "Command already queued." : "Command queued."} The worker reports the applied state below.
        </p>}
      </>}
      {history.length > 0 && (
        <div className="fuzzchanges">
          <h4>Settings changes</h4>
          <ChangeList changes={history.slice(-3).reverse()} />
          {history.length > 3 && <details>
            <summary>Earlier changes ({history.length - 3})</summary>
            <ChangeList changes={history.slice(0, -3).reverse()} />
          </details>}
        </div>
      )}
    </section>
  );
}

function ChangeList({ changes }: { changes: FuzzControlStateOut["changes"] }) {
  return <ul className="fuzzchangelist">
    {changes.map((change, index) => <li key={index}>
      <span className="muted">Iteration {change.iteration}</span>
      {Object.entries(change.applied).map(([name, value]) => <div key={name}>
        {optionLabel(name)}: {displayOptionValue(value)} <span className="muted">applied</span>
      </div>)}
      {change.rejected && <div className="fuzzrejected">
        {Object.entries(change.requested).filter(([name]) => !Object.hasOwn(change.applied, name))
          .map(([name, value]) => `${optionLabel(name)}: ${displayOptionValue(value)}`).join(" · ")}
        {" - "}{change.rejected}
      </div>}
    </li>)}
  </ul>;
}

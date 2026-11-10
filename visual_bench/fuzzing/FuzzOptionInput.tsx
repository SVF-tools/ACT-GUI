import type { FuzzOptionOut } from "./api";
import { choiceLabel, optionLabel, parseNumber, validOption, WEIGHTS, type FuzzOptionValue } from "./options";
import "./fuzzing.css";

/** Shared launch/live input anatomy; constraints and choices belong to the engine schema. */
export function FuzzOptionInput({ option, value, onChange, disabled = false }: {
  option: FuzzOptionOut; value: FuzzOptionValue | undefined; onChange: (value: FuzzOptionValue) => void; disabled?: boolean;
}) {
  const label = optionLabel(option.name);
  if (option.kind === "weights") {
    const weights = (value ?? {}) as Record<string, number>;
    const total = WEIGHTS.reduce((sum, name) => sum + (weights[name] ?? 0), 0);
    return (
      <fieldset className="fuzzweights" disabled={disabled}>
        <legend title={option.description}>{label} <small>relative; 0 disables an operator</small></legend>
        <div className="fuzzgrid">
          {WEIGHTS.map((name) => (
            <label key={name}>{name} {total > 0 && <small>{Math.round((weights[name] ?? 0) / total * 100)}%</small>}
              <input type="number" min={option.minimum ?? 0} max={option.maximum ?? undefined} step="any"
                value={Number.isFinite(weights[name]) ? weights[name] : ""}
                onChange={(e) => onChange({ ...weights, [name]: parseNumber(e.target.value) })} />
            </label>
          ))}
        </div>
        {!disabled && !validOption(option, value) && <p className="note state bad">Use nonnegative weights with at least one above 0.</p>}
      </fieldset>
    );
  }
  return (
    <label className={option.kind === "bool" ? "check" : undefined} title={option.description}>
      {option.kind !== "bool" && label}
      {option.kind === "bool" ? (
        <input type="checkbox" checked={value === true} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
      ) : option.kind === "choice" ? (
        <select value={String(value ?? "")} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
          {option.choices.map((choice) => <option key={choice} value={choice}>{choiceLabel(choice)}</option>)}
        </select>
      ) : (
        <input type="number" min={option.minimum ?? undefined} max={option.maximum ?? undefined}
          step={option.kind === "int" ? 1 : "any"} value={typeof value === "number" && Number.isFinite(value) ? value : ""}
          disabled={disabled} aria-invalid={!disabled && !validOption(option, value)}
          onChange={(e) => onChange(parseNumber(e.target.value))} />
      )}
      {option.kind === "bool" && label}
    </label>
  );
}

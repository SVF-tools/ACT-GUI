// verify_bab_batched settings of a BaB run, grouped and collapsed as ACT's bab_options groups them.
import type { BabOptionOut } from "../generated/wire";
import { BAB_GROUPS, babOptionLabel, babValid, type BabValue, type BabValues } from "./babSettings";
import { BAB_TIER_LABEL } from "./labels";

const GROUP_LABEL: Record<string, string> = { search: "Search", dual: "Dual bounds", advanced: "Advanced" };

export function BabSettings({ options, value, defaults, onChange }: {
  options: BabOptionOut[]; value: BabValues; defaults: BabValues; onChange: (v: BabValues) => void;
}) {
  const set = (name: string, v: BabValue) => onChange({ ...value, [name]: v });
  const modified = (list: BabOptionOut[]) => list.some((o) => value[o.name] !== defaults[o.name]);
  const lp = value.bab_solver_tier === "lp";
  const groups = [...BAB_GROUPS, ...new Set(options.map((o) => o.group).filter((g) => !(BAB_GROUPS as readonly string[]).includes(g)))];
  const inGroup = (group: string) => options.filter((o) => o.group === group);

  return (
    <div className="fuzzsettings babsettings">
      {inGroup("bounding").map((o) => o.name === "bab_solver_tier" ? (
        <label key={o.name} className="wide" title={o.description}>Bounding
          <select value={String(value[o.name])} onChange={(e) => set(o.name, e.target.value)}>
            {o.choices.map((c) => <option key={c} value={c}>{BAB_TIER_LABEL[c] ?? c}</option>)}
          </select>
        </label>
      ) : <BabOptionInput key={o.name} option={o} value={value[o.name]} onChange={(v) => set(o.name, v)} />)}
      {groups.filter((g) => g !== "bounding" && inGroup(g).length > 0).map((group) => {
        const list = inGroup(group);
        const off = group === "dual" && lp;
        return (
          <details key={group} className="fuzzadvanced" open={(modified(list) && !off) || undefined}>
            <summary>{GROUP_LABEL[group] ?? group} {modified(list) && <span className="chip">modified</span>}</summary>
            {off && <p className="note">Only the dual tiers use these settings.</p>}
            <div className="fuzzgrid">
              {list.map((o) => <BabOptionInput key={o.name} option={o} value={value[o.name]} disabled={off}
                onChange={(v) => set(o.name, v)} />)}
            </div>
          </details>
        );
      })}
      <button type="button" disabled={!modified(options)} onClick={() => onChange(defaults)}>Reset to ACT defaults</button>
    </div>
  );
}

function BabOptionInput({ option, value, onChange, disabled = false }: {
  option: BabOptionOut; value: BabValue | undefined; onChange: (v: BabValue) => void; disabled?: boolean;
}) {
  const label = babOptionLabel(option.name);
  if (option.kind === "bool") {
    return (
      <label className="check" title={option.description}>
        <input type="checkbox" checked={value === true} disabled={disabled} onChange={(e) => onChange(e.target.checked)} />
        {label}
      </label>
    );
  }
  if (option.kind === "choice") {
    return (
      <label title={option.description}>{label}
        <select value={String(value ?? "")} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
          {option.choices.map((c) => <option key={c} value={c}>{c.replaceAll("_", " ")}</option>)}
        </select>
      </label>
    );
  }
  return (
    <label title={option.description}>{label}
      <input type="number" min={option.minimum ?? undefined} max={option.maximum ?? undefined}
        step={option.kind === "int" ? 1 : "any"} value={typeof value === "number" && Number.isFinite(value) ? value : ""}
        disabled={disabled} aria-invalid={!disabled && !babValid(option, value)}
        onChange={(e) => onChange(e.target.value === "" ? Number.NaN : Number(e.target.value))} />
    </label>
  );
}

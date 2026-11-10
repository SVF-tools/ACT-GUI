// Keep the launch request shape; ACT's schema owns editable constraints and defaults.
import type { FuzzMutationWeights, FuzzOptions } from "../generated/wire";
import { useFuzzOptions } from "./hooks";
import { FuzzOptionInput } from "./FuzzOptionInput";
import { launchName, launchOptions } from "./options";

export type FuzzSettingsValue = Required<Omit<FuzzOptions, "mutation_weights">> & {
  mutation_weights: Required<FuzzMutationWeights>;
};

export function FuzzSettings({ value, defaults, onChange }: {
  value: FuzzSettingsValue; defaults: FuzzSettingsValue; onChange: (v: FuzzSettingsValue) => void;
}) {
  const schema = useFuzzOptions();
  const options = launchOptions(defaults, schema.data?.options);
  const basic = new Set(["max_iterations", "rng_seed", "stop_on_first"]);
  const changed = JSON.stringify(value) !== JSON.stringify(defaults);
  const input = (option: typeof options[number]) => {
    const name = launchName(option.name) as keyof FuzzSettingsValue;
    return <FuzzOptionInput key={name} option={option} value={value[name]}
      disabled={name === "perturb_scale" && value.perturb_mode === "fixed"}
      onChange={(next) => onChange({ ...value, [name]: next })} />;
  };
  return (
    <div className="fuzzsettings">
      {options.filter((option) => basic.has(launchName(option.name))).map(input)}
      <details className="fuzzadvanced" open={changed || undefined}>
        <summary>ACTFuzzer hyperparameters {changed && <span className="chip">modified</span>}</summary>
        <div className="fuzzgrid">
          {options.filter((option) => !basic.has(launchName(option.name))).map(input)}
        </div>
        <button type="button" className="secondary" disabled={!changed} onClick={() => onChange(defaults)}>Reset to ACT defaults</button>
      </details>
    </div>
  );
}

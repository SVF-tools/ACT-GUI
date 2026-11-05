import type { FuzzingOut } from "../generated/wire";

export function FuzzStrategies({ f }: { f: FuzzingOut }) {
  const total = f.strategies.reduce((a, s) => a + s.selected, 0) || 1;
  return (
    <>
      <h3>Mutation strategies <small>weights from ACT's fuzzing config</small></h3>
      <table className="tbl">
        <thead><tr><th>strategy</th><th>weight</th><th>iterations</th><th>share</th><th>violations</th></tr></thead>
        <tbody>
          {f.strategies.map((s) => (
            <tr key={s.name} className={s.weight === 0 && s.selected === 0 ? "muted" : ""}>
              <td>{s.name}</td><td className="mono">{s.weight}</td><td className="mono">{s.selected}</td>
              <td><span className="track share"><span className="bar after" style={{ left: 0, width: `${(s.selected / total) * 100}%` }} /></span></td>
              <td className={s.violations ? "mono state bad" : "mono"}>{s.violations}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

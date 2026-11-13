// Dataset sentences whose reconstructed embeddings lie nearest to a point of the model input space.
// The point is never decoded into text: these are known examples, listed with their distance.
import type { InputNeighbourOut } from "../../generated/wire";
import { fmt } from "../wire";

export function Neighbours({ items, classNames, pending, error }: {
  items: InputNeighbourOut[]; classNames: string[]; pending: boolean; error: string | null;
}) {
  return (
    <div className="neighbourbox">
      <h4>Nearest known sentences</h4>
      <p className="note">The counterexample is a point in embedding space, not a sentence. These are the nearest dataset
        sentences with recorded embeddings.</p>
      {pending && <div className="note">Finding neighbours…</div>}
      {error && <div className="error">{error}</div>}
      <ol className="neighbours">
        {items.map((n) => (
          <li key={n.example_id}>
            <span className="sentence">{n.text}</span>
            {n.label !== null && <span className="chip">{classNames[n.label] ?? n.label}</span>}
            <span className="muted mono">{n.split ? `${n.split.replace("_", " ")} · ` : ""}distance {fmt(n.distance, 3)}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

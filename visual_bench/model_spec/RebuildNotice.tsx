// Shown instead of the network when the active ACT engine cannot load a built model (e.g. after a branch switch).
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { BuiltWithOut, ModelSummary } from "../generated/wire";
import { keys } from "../shared/queryClient";
import { useRebuildModel } from "./hooks";

export function builtWithLabel(b: BuiltWithOut | null | undefined): string {
  if (!b) return "an ACT engine that was not recorded";
  const where = b.kind === "baseline" ? "the pinned baseline" : `${b.remote ?? "?"}/${b.branch ?? "?"}`;
  return `${where} (ACT ${b.commit?.slice(0, 8) ?? "?"})`;
}

export function RebuildNotice({ model, message, onRebuilt }: {
  model: ModelSummary; message: string; onRebuilt: (m: ModelSummary) => void;
}) {
  const rebuild = useRebuildModel();
  const client = useQueryClient();
  // The failed describe recorded load_failed on the server; refresh the list so its chip shows it.
  useEffect(() => { void client.invalidateQueries({ queryKey: keys.models(), exact: true }); }, [client, model.model_id]);
  return (
    <div className="banner warn">
      <div><b>This ACT engine cannot load {model.model_id}.</b> It was built on {builtWithLabel(model.built_with)}; the active
        engine reads its net file differently.</div>
      <div className="mono muted">{message}</div>
      <div className="bannerrow">
        <span>Rebuilding runs the same source settings through the active engine and loads the result as a new model; the old one and its runs stay as they are.</span>
        <button className="primary" disabled={rebuild.isPending}
          onClick={() => rebuild.mutate(model.model_id, { onSuccess: onRebuilt })}>
          {rebuild.isPending ? "Rebuilding through ACT…" : "Rebuild on this engine"}
        </button>
      </div>
      {rebuild.error && <div className="error">{rebuild.error.message}</div>}
    </div>
  );
}

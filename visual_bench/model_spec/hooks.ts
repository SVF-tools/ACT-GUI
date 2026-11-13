// Queries/mutations for /api/models, /api/models/{id}, /api/models/{id}/rebuild, /api/sources, /api/sources/sample and
// /api/models/{id}/provenance (+ /nearest).
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { InputProvenanceOut } from "../generated/wire";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useModels = () => useQuery({ queryKey: keys.models(), queryFn: api.models });
export const useModel = (id: string | null) =>
  useQuery({ queryKey: keys.model(id), queryFn: () => api.model(id!), enabled: id !== null });
export const useSources = () => useQuery({ queryKey: keys.sources(), queryFn: api.sources });
export const useSample = (dataset: string | null, index: number) =>
  useQuery({ queryKey: keys.sample(dataset, index), queryFn: () => api.sample(dataset!, index), enabled: dataset !== null });
export const useProvenance = (id: string | null) =>
  useQuery({ queryKey: keys.provenance(id), queryFn: () => api.provenance(id!), enabled: id !== null });

/** ACT's provenance of one input row (source sentence, class names, source point), or null when there is none. */
export function useRowProvenance(id: string | null, row: number): InputProvenanceOut | null {
  const q = useProvenance(id);
  return q.status === "success" && q.data.status === "available" ? q.data.rows[row] ?? null : null;
}

/** Known examples nearest to a point of the model input space; disabled while point is null. */
export function useNearest(id: string | null, row: number, point: number[] | null) {
  const key = point ? point.map((v) => v.toPrecision(9)).join(",") : "";
  const body = point && point.length > 0
    ? { row, point: [point[0]!, ...point.slice(1)] as [number, ...number[]], k: 3 } : null;
  return useQuery({ queryKey: keys.nearest(id, row, key), queryFn: () => api.nearest(id!, body!),
    enabled: id !== null && body !== null });
}

// What each ACT input row of a batched model is: a test image (torch batch) or a VNN-LIB property on one network.
export type BatchRows = { noun: "image" | "property"; labels: string[]; images: number[] | null };

export function batchRows(p: Record<string, unknown> | undefined): BatchRows | null {
  if (typeof p?.indices === "string") {
    const images = p.indices.split(",").map(Number);
    return { noun: "image", labels: images.map((x) => `#${x}`), images };
  }
  if (typeof p?.vnnlibs === "string") return { noun: "property", labels: p.vnnlibs.split(",").map(fileStem), images: null };
  return null;
}

export function useBatchRows(modelId: string | null): BatchRows | null {
  const models = useModels();
  return batchRows(models.status === "success" ? models.data.find((m) => m.model_id === modelId)?.params : undefined);
}

export function fileStem(path: string): string {
  return path.split("/").at(-1)!.replace(/\.(onnx|vnnlib)$/, "");
}

/** Name of an instance's network: its ONNX file, or the files of a multi-network property (comma-separated paths). */
export function netStem(onnx: string): string {
  return onnx.split(",").map(fileStem).join(" + ");
}

export function useRebuildModel() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.rebuildModel,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.models() }),
  });
}

export function useLoadModel() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.loadModel,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.models() }),
  });
}

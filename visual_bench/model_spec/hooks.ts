// Queries/mutations for /api/models, /api/models/{id}, /api/models/{id}/rebuild, /api/sources and /api/sources/sample.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useModels = () => useQuery({ queryKey: keys.models(), queryFn: api.models });
export const useModel = (id: string | null) =>
  useQuery({ queryKey: keys.model(id), queryFn: () => api.model(id!), enabled: id !== null });
export const useSources = () => useQuery({ queryKey: keys.sources(), queryFn: api.sources });
export const useSample = (dataset: string | null, index: number) =>
  useQuery({ queryKey: keys.sample(dataset, index), queryFn: () => api.sample(dataset!, index), enabled: dataset !== null });

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

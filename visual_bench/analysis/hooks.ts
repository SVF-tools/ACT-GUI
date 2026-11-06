// Query: GET /api/runs/{id}/layers.
import { useSyncExternalStore } from "react";
import { onlineManager, useQueries, useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { layers, propagation, propagationLayer, type PropagationSlice } from "./api";
import type { PropagationRecordOut } from "../generated/wire";

const subscribeOnline = (listener: () => void) => onlineManager.subscribe(listener);
export const useAnalysisOnline = () => useSyncExternalStore(subscribeOnline, () => onlineManager.isOnline());

export const useLayers = (id: string | null) =>
  useQuery({ queryKey: keys.layers(id), queryFn: () => layers(id!), enabled: id !== null });

export const usePropagation = (id: string | null) =>
  useQuery({ queryKey: keys.propagation(id), queryFn: () => propagation(id!), enabled: id !== null });

/** Fetch only the exact identities visible at this replay cursor. Events invalidate the run prefix. */
export function usePropagationRecords(id: string | null, layer: number | null, selected: PropagationRecordOut[],
  slice: PropagationSlice = {}) {
  const filters = [...new Map(selected.filter((r) => r.key && r.key.layer_id === layer).map((r) => {
    const k = r.key!;
    return [JSON.stringify([k.scope, k.pass_, k.stage, k.version]), k] as const;
  })).values()];
  const queries = useQueries({ queries: filters.map((k) => ({
    queryKey: keys.propagationLayer(id, layer, k.scope, k.pass_, k.stage, k.version, slice.fields?.join(",") ?? null, slice.neuron ?? null),
    queryFn: () => propagationLayer(id!, layer!, k, slice),
    enabled: id !== null && layer !== null,
  })) });
  const ids = new Set(selected.map((r) => r.record_id));
  return {
    records: [...new Map(queries.flatMap((q) => q.data?.records ?? []).filter((r) => ids.has(r.record_id)).map((r) => [r.record_id, r])).values()].sort((a, b) => a.record_id - b.record_id),
    pending: queries.some((q) => q.isPending),
    error: queries.find((q) => q.error)?.error,
    retry: () => { for (const q of queries) void q.refetch(); },
  };
}

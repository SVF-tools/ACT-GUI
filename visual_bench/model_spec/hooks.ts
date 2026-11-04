// Queries/mutations for /api/models, /api/models/{id}, /api/sources and /api/sources/sample.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useModels = () => useQuery({ queryKey: keys.models(), queryFn: api.models });
export const useModel = (id: string | null) =>
  useQuery({ queryKey: keys.model(id), queryFn: () => api.model(id!), enabled: id !== null });
export const useSources = () => useQuery({ queryKey: keys.sources(), queryFn: api.sources });
export const useSample = (dataset: string | null, index: number) =>
  useQuery({ queryKey: keys.sample(dataset, index), queryFn: () => api.sample(dataset!, index), enabled: dataset !== null });

export function useLoadModel() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.loadModel,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.models() }),
  });
}

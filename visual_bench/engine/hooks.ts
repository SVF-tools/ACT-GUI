// Queries/commands for /api/engine, /api/solvers/gurobi and /api/solvers/gurobi/license.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useEngine = () => useQuery({ queryKey: keys.engine(), queryFn: api.engine });
export const useGurobi = () => useQuery({ queryKey: keys.gurobi(), queryFn: api.gurobi });

export function useUploadGurobiLicense() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.uploadGurobiLicense,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.gurobi() }),
  });
}

export function useRemoveGurobiLicense() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.removeGurobiLicense,
    onSuccess: () => client.invalidateQueries({ queryKey: keys.gurobi() }),
  });
}

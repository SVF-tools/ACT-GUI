// Queries/commands for /api/runs, /api/runs/{id}, /stop; SSE at /api/runs/{id}/events.
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { followRun } from "../shared/http";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useRuns = () => useQuery({ queryKey: keys.runs(), queryFn: api.runs });
export const useRun = (id: string | null) =>
  useQuery({ queryKey: keys.run(id), queryFn: () => api.run(id!), enabled: id !== null });

export function useStartRun() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.startRun,
    onSuccess: async (run) => {
      client.setQueryData(keys.run(run.run_id), run);
      await client.invalidateQueries({ queryKey: keys.runs() });
    },
  });
}

export function useStopRun() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.stopRun,
    onSuccess: async (run) => {
      await Promise.all([
        client.invalidateQueries({ queryKey: keys.run(run.run_id) }),
        client.invalidateQueries({ queryKey: keys.runs() }),
      ]);
    },
  });
}

/** One subscription per active run, including runs in modes not currently visible. */
export function useLiveRuns() {
  const client = useQueryClient();
  const runs = useRuns();
  const activeIds = (runs.data?.runs ?? [])
    .filter((r) => r.status === "queued" || r.status === "running")
    .map((r) => r.run_id).sort().join(",");
  useEffect(() => {
    if (!activeIds) return;
    const stops = activeIds.split(",").map((id) => followRun(id, () => {
      // The run prefix also refreshes fuzzing, layer states, coverage and record views.
      void client.invalidateQueries({ queryKey: keys.run(id) });
      void client.invalidateQueries({ queryKey: keys.runs() });
    }));
    return () => stops.forEach((stop) => stop());
  }, [activeIds, client]);
}

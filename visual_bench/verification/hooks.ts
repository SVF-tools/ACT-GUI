// Queries/commands for /api/verification/defaults, /api/runs, /api/runs/{id}, /stop, /saved-counterexample; SSE at /api/runs/{id}/events.
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { followRun } from "../shared/http";
import { keys } from "../shared/queryClient";
import * as api from "./api";
import type { VerifySettingsValue } from "./VerifySettings";

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

export function useSaveRunCounterexample() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, row }: { id: string; row: number | null }) => api.saveCounterexample(id, row),
    onSuccess: (run) => client.setQueryData(keys.run(run.run_id), run),
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

export const useVerificationDefaults = () =>
  useQuery({ queryKey: keys.verificationDefaults(), queryFn: api.verificationDefaults });

/** verify_once settings (dual / hybridz) edited in the run form; null until the defaults arrive. */
export function useVerifyConfiguration() {
  const query = useVerificationDefaults();
  const defaults = query.isSuccess ? query.data as VerifySettingsValue : null;
  const [draft, setValue] = useState<VerifySettingsValue | null>(null);
  return { query, defaults, value: draft ?? defaults, setValue };
}

// Queries: GET /api/runs/{id}/coverage, /bab and /bab/nodes/{node_id}. Keys sit under the run prefix, so the run's
// committed SSE events (verify.bab while BaB runs) refetch them through useLiveRuns.
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { babNode, babTree, coverage } from "./api";

export const useCoverage = (id: string | null) =>
  useQuery({ queryKey: keys.coverage(id), queryFn: () => coverage(id!), enabled: id !== null });

// The previous tree stays on screen while a live refetch or a new subtree focus loads.
export const useBabTree = (id: string | null, root: number) =>
  useQuery({ queryKey: keys.babTree(id, root), queryFn: () => babTree(id!, root), enabled: id !== null,
    placeholderData: keepPreviousData });

export const useBabNode = (id: string | null, node: number | null) =>
  useQuery({ queryKey: keys.babNode(id, node), queryFn: () => babNode(id!, node!), enabled: id !== null && node !== null,
    placeholderData: keepPreviousData });

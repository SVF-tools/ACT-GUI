// Query: GET /api/runs/{id}/layers.
import { useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { layers } from "./api";

export const useLayers = (id: string | null) =>
  useQuery({ queryKey: keys.layers(id), queryFn: () => layers(id!), enabled: id !== null });

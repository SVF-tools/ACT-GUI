// Query: GET /api/runs/{id}/coverage.
import { useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { coverage } from "./api";

export const useCoverage = (id: string | null) =>
  useQuery({ queryKey: keys.coverage(id), queryFn: () => coverage(id!), enabled: id !== null });

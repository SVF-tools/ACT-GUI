// Query: GET /api/runs/{id}; shares the lifecycle cache key with verification.
import { useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { run } from "./api";

export const useRecord = (id: string | null) =>
  useQuery({ queryKey: keys.run(id), queryFn: () => run(id!), enabled: id !== null });

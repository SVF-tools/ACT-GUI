// Query/command: /api/assistant/providers and /api/assistant/explain (read-only frozen context).
import { useMutation, useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import * as api from "./api";

export const useProviders = () => useQuery({ queryKey: keys.providers(), queryFn: api.providers });
export const useExplain = () => useMutation({ mutationFn: api.explain });

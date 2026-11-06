// Query: POST /api/presence every 20 s; the server counts browsers seen inside its window.
import { useQuery } from "@tanstack/react-query";
import { keys } from "../shared/queryClient";
import { heartbeat } from "./api";

const ID_KEY = "act-gui.presence-id";

// One id per browser (localStorage), so several tabs count as one visitor.
function browserId(): string {
  let id = localStorage.getItem(ID_KEY);
  if (!id) {
    id = typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) => b.toString(16).padStart(2, "0")).join("");
    localStorage.setItem(ID_KEY, id);
  }
  return id;
}

export const usePresence = () =>
  useQuery({
    queryKey: keys.presence(),
    queryFn: () => heartbeat(browserId()),
    refetchInterval: 20_000,
    refetchIntervalInBackground: true,
  });

import { useEffect, useRef, useState } from "react";
import { LatestRequest } from "./selection";

export type QueryState<T> = { status: "idle" } | { status: "loading" } | { status: "ok"; data: T } | { status: "error"; message: string };

/** Fetch for a key; a response for an older key is discarded (WS-02 stale-response rule). */
export function useQuery<T>(key: string | null, fetcher: () => Promise<T>, refresh = 0): QueryState<T> {
  const guard = useRef(new LatestRequest());
  const [state, setState] = useState<QueryState<T>>({ status: "idle" });
  useEffect(() => {
    if (key === null) {
      guard.current.begin();
      setState({ status: "idle" });
      return;
    }
    const token = guard.current.begin();
    setState({ status: "loading" });
    fetcher().then(
      (data) => guard.current.isCurrent(token) && setState({ status: "ok", data }),
      (e: unknown) => guard.current.isCurrent(token) && setState({ status: "error", message: e instanceof Error ? e.message : String(e) }),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, refresh]);
  return state;
}

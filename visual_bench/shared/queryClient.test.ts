import { QueryClient, QueryObserver } from "@tanstack/react-query";
import { describe, expect, it } from "vitest";
import { keys } from "./queryClient";

describe("selection-keyed queries", () => {
  it("keeps a late response for an older selection out of the selected view", async () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
    let releaseA!: (value: string) => void;
    const slowA = new Promise<string>((resolve) => { releaseA = resolve; });
    const fetchA = () => slowA;
    const requestA = client.fetchQuery({ queryKey: keys.model("a"), queryFn: fetchA });
    const observer = new QueryObserver(client, { queryKey: keys.model("a"), queryFn: fetchA });
    let observedB!: () => void;
    const readyB = new Promise<void>((resolve) => { observedB = resolve; });
    const unsubscribe = observer.subscribe((result) => {
      if (result.isSuccess && result.data === "B") observedB();
    });
    try {
      observer.setOptions({ queryKey: keys.model("b"), queryFn: async () => "B" });
      await readyB;
      releaseA("A");
      await requestA;
      expect(observer.getCurrentResult().data).toBe("B");
      expect(client.getQueryData(keys.model("a"))).toBe("A");
    } finally {
      unsubscribe();
      client.clear();
    }
  });

  it("invalidates all projections of one run without touching other runs or the list", async () => {
    const client = new QueryClient();
    const related = [keys.run("a"), keys.fuzzing("a"), keys.layers("a"), keys.coverage("a")];
    const unrelated = [keys.run("b"), keys.fuzzing("b"), keys.runs(), keys.models()];
    try {
      for (const key of [...related, ...unrelated]) client.setQueryData(key, {});
      await client.invalidateQueries({ queryKey: keys.run("a") });
      for (const key of related) expect(client.getQueryState(key)?.isInvalidated).toBe(true);
      for (const key of unrelated) expect(client.getQueryState(key)?.isInvalidated).toBe(false);
    } finally {
      client.clear();
    }
  });
});

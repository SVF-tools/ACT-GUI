import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import type { Pass } from "./propagation";

type ViewState = { cursor: number | null; pass: Pass; lane: number; level: "network" | "layer" | "neuron" };
const initial: ViewState = { cursor: null, pass: "forward", lane: 0, level: "network" };
const Context = createContext<{ state: ViewState; update: (next: Partial<ViewState>) => void }>({ state: initial, update: () => {} });
export function PropagationProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState(initial);
  const update = useCallback((next: Partial<ViewState>) => setState((s) => ({ ...s, ...next })), []);
  return <Context.Provider value={{ state, update }}>{children}</Context.Provider>;
}
export const usePropagationSelection = () => useContext(Context);

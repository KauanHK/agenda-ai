// Tiny zustand-like store without external deps.
import { useSyncExternalStore } from "react";

type Setter<S> = (partial: Partial<S> | ((s: S) => Partial<S>)) => void;
type Init<S> = (set: Setter<S>, get: () => S) => S;

export function create<S extends object>(init: Init<S>) {
  let state: S;
  const listeners = new Set<() => void>();

  const set: Setter<S> = (partial) => {
    const next = typeof partial === "function" ? (partial as (s: S) => Partial<S>)(state) : partial;
    state = { ...state, ...next };
    listeners.forEach((l) => l());
  };
  const get = () => state;
  state = init(set, get);

  function useStore(): S;
  function useStore<U>(selector: (s: S) => U): U;
  function useStore<U>(selector?: (s: S) => U) {
    const subscribe = (cb: () => void) => {
      listeners.add(cb);
      return () => { listeners.delete(cb); };
    };
    return useSyncExternalStore(
      subscribe,
      () => (selector ? selector(state) : (state as unknown as U)),
    );
  }
  return useStore;
}

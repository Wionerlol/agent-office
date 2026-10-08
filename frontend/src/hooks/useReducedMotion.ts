import { useSyncExternalStore } from "react";

const QUERY = "(prefers-reduced-motion: reduce)";
const snapshot = () => window.matchMedia?.(QUERY).matches ?? false;
const subscribe = (notify: () => void) => {
  const media = window.matchMedia?.(QUERY);
  media?.addEventListener("change", notify);
  return () => media?.removeEventListener("change", notify);
};

/** One App-owned preference subscription; renderers receive the same setting. */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(subscribe, snapshot, () => false);
}

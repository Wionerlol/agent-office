import { useEffect } from "react";
import { INTERACTION_SWEEP_MS } from "../models/interaction";
import { useAgentStore } from "../store/agents";

/** One owner for all cue expiry/offline grace, independent of simulation pause. */
export function useInteractionCleanup(): void {
  useEffect(() => {
    const sweep = () => useAgentStore.getState().sweepInteractions();
    sweep();
    const interval = window.setInterval(sweep, INTERACTION_SWEEP_MS);
    return () => window.clearInterval(interval);
  }, []);
}

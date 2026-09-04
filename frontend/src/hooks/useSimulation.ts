import { useEffect } from "react";

import { AGENT_STATES } from "../models/agent";
import { useAgentStore } from "../store/agents";

const SIMULATION_STATES = AGENT_STATES.filter((state) => state !== "offline" && state !== "starting");

export function useSimulation(enabled: boolean) {
  const paused = useAgentStore((state) => state.simulationPaused);

  useEffect(() => {
    if (!enabled || paused) return;
    let timeout: number;
    const tick = () => {
      timeout = window.setTimeout(() => {
        const { agents, setAgentStatus, addEvent } = useAgentStore.getState();
        const current = Object.values(agents);
        if (current.length) {
          const agent = current[Math.floor(Math.random() * current.length)];
          const status = SIMULATION_STATES[Math.floor(Math.random() * SIMULATION_STATES.length)];
          setAgentStatus(agent.id, status);
          addEvent({ type: "agent.state_changed", agent_id: agent.id, timestamp: new Date().toISOString(), payload: { to: status } });
        }
        tick();
      }, 5000 + Math.floor(Math.random() * 5001));
    };
    tick();
    return () => window.clearTimeout(timeout);
  }, [enabled, paused]);
}

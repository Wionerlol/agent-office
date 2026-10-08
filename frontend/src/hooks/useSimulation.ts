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
        const { agents, updateAgent, addEvent } = useAgentStore.getState();
        const current = Object.values(agents);
        if (current.length) {
          const agent = current[Math.floor(Math.random() * current.length)];
          const status = SIMULATION_STATES[Math.floor(Math.random() * SIMULATION_STATES.length)];
          const waiting = status === "waiting";
          const child = waiting && agent.id === "lead" && agents.tester ? "tester" : null;
          const timestamp = new Date().toISOString();
          const context = {
            waiting_reason: waiting ? (child ? "child_agent" : "user_input") : null,
            waiting_on_agent_id: child,
          };
          updateAgent(agent.id, { status, last_active_at: timestamp, ...context });
          addEvent({ type: "agent.state_changed", agent_id: agent.id, timestamp, payload: { to: status, ...context } });
        }
        tick();
      }, 5000 + Math.floor(Math.random() * 5001));
    };
    tick();
    return () => window.clearTimeout(timeout);
  }, [enabled, paused]);
}

import { useEffect, useRef } from "react";
import { applyServerMessage } from "../api/websocket";
import { demoAgents } from "../data/demo";
import { useAgentStore } from "../store/agents";

const STEP_DELAYS = [3000, 4000, 7000, 3000, 6000, 4000] as const;

/** Scripted normalized messages exercise the same lifecycle path as the server. */
export function useSimulation(enabled: boolean) {
  const paused = useAgentStore((state) => state.simulationPaused);
  const step = useRef(0);
  useEffect(() => {
    if (!enabled || paused) return;
    let timeout: number;
    const tick = () => {
      timeout = window.setTimeout(() => {
        const timestamp = new Date().toISOString();
        switch (step.current) {
          case 0:
            applyServerMessage({ type: "agent.started", agent: { ...demoAgents[1], id: "demo-tester", name: "Test Partner", status: "testing", started_at: timestamp, last_active_at: timestamp } });
            break;
          case 1:
            applyServerMessage({ type: "agent.updated", agent_id: "lead", changes: { status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id: "demo-tester", last_active_at: timestamp } });
            break;
          case 2:
            applyServerMessage({ type: "agent.updated", agent_id: "demo-tester", changes: { status: "done", current_tool: null, last_active_at: timestamp } });
            break;
          case 3:
            applyServerMessage({ type: "agent.updated", agent_id: "lead", changes: { status: "thinking", waiting_reason: null, waiting_on_agent_id: null, last_active_at: timestamp } });
            applyServerMessage({ type: "agent.stopped", agent_id: "demo-tester" });
            break;
          case 4:
            applyServerMessage({ type: "agent.updated", agent_id: "reviewer", changes: { status: "error", last_active_at: timestamp } });
            break;
          case 5:
            applyServerMessage({ type: "agent.updated", agent_id: "reviewer", changes: { status: "thinking", last_active_at: timestamp } });
        }
        step.current = (step.current + 1) % STEP_DELAYS.length;
        tick();
      }, STEP_DELAYS[step.current]);
    };
    tick();
    return () => window.clearTimeout(timeout);
  }, [enabled, paused]);
}

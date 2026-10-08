import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { applyServerMessage } from "../api/websocket";
import { demoAgents } from "../data/demo";
import { useAgentStore } from "../store/agents";
import { useSimulation } from "./useSimulation";
import { useInteractionCleanup } from "./useInteractionCleanup";

beforeEach(() => { vi.useFakeTimers(); useAgentStore.getState().reset(); applyServerMessage({ type: "snapshot", agents: demoAgents }); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });

it("script uses lifecycle messages for delegation, waiting, completion and exit", () => {
  renderHook(() => { useSimulation(true); useInteractionCleanup(); });
  act(() => vi.advanceTimersByTime(3000));
  expect(useAgentStore.getState().interactionCues).toMatchObject([{ kind: "delegation", sourceAgentId: "lead", targetAgentId: "demo-tester" }]);
  act(() => vi.advanceTimersByTime(4000));
  expect(useAgentStore.getState().agents.lead).toMatchObject({ status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id: "demo-tester", role: "lead" });
  act(() => vi.advanceTimersByTime(7000));
  expect(useAgentStore.getState().interactionCues).toMatchObject([{ kind: "handoff", sourceAgentId: "demo-tester", targetAgentId: "lead" }]);
  act(() => vi.advanceTimersByTime(3000));
  expect(useAgentStore.getState().agents.lead).toMatchObject({ status: "thinking", waiting_reason: null, waiting_on_agent_id: null, role: "lead" });
  act(() => vi.advanceTimersByTime(5000));
  expect(useAgentStore.getState().agents["demo-tester"]).toBeUndefined();
  expect(useAgentStore.getState().agents.frontend).toMatchObject({ status: "waiting", waiting_reason: "user_input" });
});

it("pause stops scripted changes, resume preserves the step, unmount cleans timers", () => {
  const hook = renderHook(() => useSimulation(true));
  act(() => vi.advanceTimersByTime(3000));
  act(() => useAgentStore.getState().setSimulationPaused(true));
  const initial = useAgentStore.getState().agents;
  act(() => vi.advanceTimersByTime(20000));
  expect(useAgentStore.getState().agents).toBe(initial);
  act(() => useAgentStore.getState().setSimulationPaused(false));
  act(() => vi.advanceTimersByTime(4000));
  expect(useAgentStore.getState().agents.lead.waiting_on_agent_id).toBe("demo-tester");
  hook.unmount();
  expect(vi.getTimerCount()).toBe(0);
});

import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { demoAgents } from "../data/demo";
import { useAgentStore } from "../store/agents";
import { useSimulation } from "./useSimulation";

beforeEach(() => { vi.useFakeTimers(); useAgentStore.getState().reset(); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.useRealTimers(); });

it("simulation produces deterministic child context and clears it when work resumes", () => {
  useAgentStore.getState().replaceAgents([demoAgents[4], demoAgents[1]]);
  vi.spyOn(Math, "random").mockReturnValueOnce(0).mockReturnValueOnce(0).mockReturnValueOnce(0.6).mockReturnValue(0);
  renderHook(() => useSimulation(true));
  act(() => vi.advanceTimersByTime(5000));
  expect(useAgentStore.getState().agents.lead).toMatchObject({ status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id: "tester", role: "lead" });
  act(() => vi.advanceTimersByTime(5000));
  expect(useAgentStore.getState().agents.lead).toMatchObject({ status: "thinking", waiting_reason: null, waiting_on_agent_id: null, role: "lead" });
});

it("pause preserves the semantic showcase instead of running a separate visual path", () => {
  useAgentStore.getState().replaceAgents(demoAgents);
  useAgentStore.getState().setSimulationPaused(true);
  const initial = useAgentStore.getState().agents;
  renderHook(() => useSimulation(true));
  act(() => vi.advanceTimersByTime(20000));
  expect(useAgentStore.getState().agents).toBe(initial);
});

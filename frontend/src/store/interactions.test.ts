import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { applyServerMessage } from "../api/websocket";
import { demoAgents } from "../data/demo";
import { CUE_TTL, MAX_CUES, MAX_START_KEYS, coordinationLinks } from "../models/interaction";
import { useInteractionCleanup } from "../hooks/useInteractionCleanup";
import { useAgentStore } from "./agents";

const parent = { ...demoAgents[4], status: "thinking" as const, waiting_reason: null, waiting_on_agent_id: null };
const child = { ...demoAgents[1], id: "child", parent_agent_id: parent.id };
const store = () => useAgentStore.getState();
const start = () => applyServerMessage({ type: "agent.started", agent: child });
const update = (status: "done" | "error" | "testing") => applyServerMessage({ type: "agent.updated", agent_id: child.id, changes: { status } });
beforeEach(() => { vi.useFakeTimers(); store().reset(); applyServerMessage({ type: "snapshot", agents: [parent] }); });
afterEach(() => { cleanup(); vi.useRealTimers(); });

it("start delegates once per generation, snapshot never replays", () => {
  start(); start();
  expect(store().interactionCues).toMatchObject([{ kind: "delegation", sourceAgentId: parent.id, targetAgentId: child.id }]);
  applyServerMessage({ type: "snapshot", agents: [parent, child] });
  start(); expect(store().interactionCues).toEqual([]);
  store().removeAgent(child.id); start(); expect(store().interactionCues).toEqual([]);
  applyServerMessage({ type: "agent.started", agent: { ...child, started_at: "new-generation" } });
  expect(store().interactionCues).toHaveLength(1);
});
it("missing or self parent never fabricates delegation/completion", () => {
  for (const parent_agent_id of ["missing", child.id, null]) {
    applyServerMessage({ type: "agent.started", agent: { ...child, parent_agent_id, started_at: String(parent_agent_id) } }); update("done");
  }
  expect(store().interactionCues).toEqual([]);
});
it("status edges produce handoff/blocked once, identical updates never restart", () => {
  applyServerMessage({ type: "snapshot", agents: [parent, child] });
  update("done"); update("done");
  expect(store().interactionCues).toMatchObject([{ kind: "handoff", sourceAgentId: child.id, targetAgentId: parent.id }]);
  update("error"); const before = store().interactionCues;
  vi.advanceTimersByTime(1000); update("error"); expect(store().interactionCues).toEqual(before);
  expect(store().agents[parent.id].status).toBe("thinking");
  applyServerMessage({ type: "snapshot", agents: [parent, { ...child, status: "done" }] });
  update("done"); expect(store().interactionCues).toEqual([]);
});
it("coordination requires current explicit visible wait", () => {
  const waiting = { ...parent, status: "waiting" as const, waiting_reason: "child_agent", waiting_on_agent_id: child.id };
  expect(coordinationLinks([waiting, child])).toEqual([{ sourceAgentId: parent.id, targetAgentId: child.id }]);
  expect(coordinationLinks([waiting])).toEqual([]);
  expect(coordinationLinks([parent, child])).toEqual([]);
  expect(coordinationLinks([{ ...waiting, waiting_reason: "user_input" }, child])).toEqual([]);
  expect(coordinationLinks([{ ...waiting, waiting_on_agent_id: parent.id }, child])).toEqual([]);
});
it("central sweep expires deterministic TTLs and cleans its timer", () => {
  applyServerMessage({ type: "snapshot", agents: [parent, child] });
  const hook = renderHook(() => useInteractionCleanup()); update("done");
  act(() => vi.advanceTimersByTime(CUE_TTL.handoff - 250)); expect(store().interactionCues).toHaveLength(1);
  act(() => vi.advanceTimersByTime(250)); expect(store().interactionCues).toEqual([]);
  update("error"); act(() => vi.advanceTimersByTime(CUE_TTL.blocked)); expect(store().interactionCues).toEqual([]);
  hook.unmount(); expect(vi.getTimerCount()).toBe(0);
});
it("cue/retired-start memory stays bounded and content-free", () => {
  for (let i = 0; i < 150; i++) applyServerMessage({ type: "agent.started", agent: { ...child, id: `child-${i}`, metadata: { private: "DO_NOT_COPY" } } });
  expect(store().interactionCues).toHaveLength(MAX_CUES);
  expect(store().knownStarts).toHaveLength(MAX_START_KEYS);
  expect(JSON.stringify(store().interactionCues)).not.toContain("DO_NOT_COPY");
});
it("stop/removal clears dependent cues; duplicate stops do not extend grace", () => {
  start(); applyServerMessage({ type: "agent.stopped", agent_id: child.id }); expect(store().interactionCues).toEqual([]);
  vi.advanceTimersByTime(4000); applyServerMessage({ type: "agent.stopped", agent_id: child.id });
  vi.advanceTimersByTime(1000); store().sweepInteractions(); expect(store().agents[child.id]).toBeUndefined();
  start(); update("done"); store().removeAgent(parent.id); expect(store().interactionCues).toEqual([]);
});
it("re-registration cancels stale offline cleanup", () => {
  start(); applyServerMessage({ type: "agent.stopped", agent_id: child.id }); vi.advanceTimersByTime(4000);
  applyServerMessage({ type: "agent.started", agent: { ...child, started_at: "next" } });
  vi.advanceTimersByTime(1000); store().sweepInteractions(); expect(store().agents[child.id].status).toBe("testing");
});

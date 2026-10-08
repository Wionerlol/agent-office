import { cleanup, renderHook } from "@testing-library/react";
import { useInteractionCleanup } from "../hooks/useInteractionCleanup";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAgentStore } from "../store/agents";
import { applyServerMessage } from "./websocket";

describe("WebSocket messages", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useAgentStore.getState().reset();
    renderHook(() => useInteractionCleanup());
  });
  afterEach(() => { cleanup(); vi.useRealTimers(); });

  it("normalizes snapshots and incremental updates into the store", () => {
    applyServerMessage({
      type: "snapshot",
      agents: [{ id: "worker", name: "Worker", provider: "codex", pid: null, repository: "/repo", worktree: null, branch: "main", status: "thinking", task: null, current_tool: null, changed_files: [], started_at: "2026-09-04T08:00:00Z", last_active_at: "2026-09-04T08:00:00Z", metadata: {} }],
    });
    applyServerMessage({ type: "agent.updated", agent_id: "worker", changes: { status: "testing" } });

    expect(useAgentStore.getState().agents.worker.status).toBe("testing");

    applyServerMessage({ type: "agent.stopped", agent_id: "worker" });
    expect(useAgentStore.getState().agents.worker.status).toBe("offline");
    applyServerMessage({
      type: "agent.started",
      agent: { ...useAgentStore.getState().agents.worker, status: "thinking" },
    });
    vi.advanceTimersByTime(5000);
    expect(useAgentStore.getState().agents.worker.status).toBe("thinking");
  });
  it("preserves semantic fields across snapshots, enrichment, and activity updates", () => {
    const agent = { id: "child", name: "Tester", provider: "codex", pid: 42,
      repository: "/repo", worktree: null, branch: null, status: "thinking" as const,
      task: "Verify auth", role: "tester", responsibilities: ["Run tests"],
      parent_agent_id: "lead", definition_id: "tester", current_tool: null,
      changed_files: [], started_at: "2026-10-02T00:00:00Z", last_active_at: "2026-10-02T00:00:00Z", metadata: {} };
    applyServerMessage({ type: "snapshot", agents: [agent] });
    applyServerMessage({ type: "agent.updated", agent_id: "child", changes: { name: "Security Tester", role: "security", responsibilities: ["Audit auth"] } });
    applyServerMessage({ type: "agent.updated", agent_id: "child", changes: { status: "testing", current_tool: "pytest" } });
    expect(useAgentStore.getState().agents.child).toMatchObject({
      name: "Security Tester", role: "security", responsibilities: ["Audit auth"],
      parent_agent_id: "lead", definition_id: "tester", status: "testing", current_tool: "pytest",
    });
  });

});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAgentStore } from "../store/agents";
import { applyHistoryEvent } from "./history";

describe("history replay", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useAgentStore.getState().reset();
  });
  afterEach(() => vi.useRealTimers());

  it("rebuilds visible state from normalized domain events", () => {
    applyHistoryEvent({
      type: "agent.started",
      agent_id: "replay-agent",
      timestamp: "2026-09-04T08:00:00Z",
      payload: { agent: { id: "replay-agent", name: "Replay", provider: "codex", pid: 5, repository: "/repo", worktree: "/repo", branch: "main", status: "thinking", task: null, current_tool: null, changed_files: [], started_at: "2026-09-04T08:00:00Z", last_active_at: "2026-09-04T08:00:00Z", metadata: {} } },
    });
    applyHistoryEvent({
      type: "agent.state_changed",
      agent_id: "replay-agent",
      timestamp: "2026-09-04T08:01:00Z",
      payload: { from: "thinking", to: "testing" },
    });

    expect(useAgentStore.getState().agents["replay-agent"].status).toBe("testing");
    expect(useAgentStore.getState().recentEvents).toHaveLength(2);
  });

  it("removes a stopped agent after its exit animation", () => {
    const now = "2026-09-04T08:00:00Z";
    useAgentStore.getState().addAgent({ id: "leaver", name: "Leaver", provider: "custom", pid: 8, repository: "/repo", worktree: null, branch: "main", status: "done", task: null, current_tool: null, changed_files: [], started_at: now, last_active_at: now, metadata: {} });

    applyHistoryEvent({ type: "agent.stopped", agent_id: "leaver", timestamp: now, payload: {} });
    expect(useAgentStore.getState().agents.leaver.status).toBe("offline");
    vi.advanceTimersByTime(1800);
    expect(useAgentStore.getState().agents.leaver).toBeUndefined();
  });
});

import { beforeEach, describe, expect, it } from "vitest";

import type { AgentEvent } from "../models/agent";
import { useAgentStore } from "../store/agents";
import { applyHistoryEvent, applyReplayAction, buildReplayTimeline, replayDelay } from "./history";

describe("history replay", () => {
  beforeEach(() => useAgentStore.getState().reset());

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

    applyHistoryEvent({
      type: "agent.tool_started",
      agent_id: "replay-agent",
      timestamp: "2026-09-04T08:01:01Z",
      payload: { tool: "search", command: ["bash", "-lc", "rg AgentState backend"] },
    });
    expect(useAgentStore.getState().agents["replay-agent"].status).toBe("searching");
  });

  it("removes a stopped agent after its exit animation", () => {
    const now = "2026-09-04T08:00:00Z";
    useAgentStore.getState().addAgent({ id: "leaver", name: "Leaver", provider: "custom", pid: 8, repository: "/repo", worktree: null, branch: "main", status: "done", task: null, current_tool: null, changed_files: [], started_at: now, last_active_at: now, metadata: {} });

    const stopped: AgentEvent = { type: "agent.stopped", agent_id: "leaver", timestamp: now, payload: {} };
    const timeline = buildReplayTimeline([stopped]);
    applyReplayAction(timeline[0]);
    expect(useAgentStore.getState().agents.leaver.status).toBe("offline");
    expect(replayDelay(timeline, 1, 5)).toBe(1000);
    applyReplayAction(timeline[1]);
    expect(useAgentStore.getState().agents.leaver).toBeUndefined();
  });
});

import { beforeEach, describe, expect, it } from "vitest";

import { useAgentStore } from "../store/agents";
import { applyHistoryEvent } from "./history";

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
  });
});

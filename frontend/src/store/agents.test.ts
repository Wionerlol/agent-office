import { beforeEach, describe, expect, it } from "vitest";

import type { Agent } from "../models/agent";
import { useAgentStore } from "./agents";

const agent: Agent = {
  id: "backend",
  name: "Backend",
  provider: "codex",
  pid: 42,
  repository: "/repo",
  worktree: null,
  branch: "main",
  status: "thinking",
  task: "Build state engine",
  current_tool: null,
  changed_files: [],
  started_at: "2026-09-04T08:00:00Z",
  last_active_at: "2026-09-04T08:00:00Z",
  metadata: {},
};

describe("agent store", () => {
  beforeEach(() => useAgentStore.getState().reset());

  it("manages agents through its public actions", () => {
    useAgentStore.getState().addAgent(agent);
    useAgentStore.getState().setAgentStatus("backend", "testing");
    useAgentStore.getState().updateAgent("backend", {
      current_tool: "pytest",
      changed_files: ["backend/state/engine.py"],
    });

    expect(useAgentStore.getState().agents.backend).toMatchObject({
      status: "testing",
      current_tool: "pytest",
    });

    useAgentStore.getState().removeAgent("backend");
    expect(useAgentStore.getState().agents).toEqual({});
  });
});

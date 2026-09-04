import { describe, expect, it } from "vitest";

import type { Agent } from "../models/agent";
import { agentsForProject } from "./selectors";

const base: Omit<Agent, "id" | "repository" | "worktree"> = {
  name: "Agent",
  provider: "codex",
  pid: null,
  branch: "main",
  status: "coding",
  task: null,
  current_tool: null,
  changed_files: [],
  started_at: "2026-09-04T08:00:00Z",
  last_active_at: "2026-09-04T08:00:00Z",
  metadata: {},
};

describe("agentsForProject", () => {
  it("includes agents attached by repository or worktree", () => {
    const agents: Agent[] = [
      { ...base, id: "main", repository: "/repo", worktree: null },
      { ...base, id: "branch", repository: "/repo", worktree: "/worktrees/branch" },
      { ...base, id: "other", repository: "/other", worktree: null },
    ];
    expect(agentsForProject(agents, "/repo").map((agent) => agent.id)).toEqual(["main", "branch"]);
    expect(agentsForProject(agents, "/worktrees/branch").map((agent) => agent.id)).toEqual(["branch"]);
  });
});

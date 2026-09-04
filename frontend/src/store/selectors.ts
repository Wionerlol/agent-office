import type { Agent } from "../models/agent";

export function agentsForProject(agents: Agent[], projectPath: string | null): Agent[] {
  if (!projectPath) return agents;
  return agents.filter(
    (agent) => agent.repository === projectPath || agent.worktree === projectPath,
  );
}

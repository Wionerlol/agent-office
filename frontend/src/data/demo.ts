import type { Agent } from "../models/agent";

const now = new Date().toISOString();
const base: Omit<Agent, "id" | "name" | "role" | "status"> = {
  provider: "demo", pid: null, repository: "agent-office", worktree: null, branch: "main",
  task: null, current_tool: null, changed_files: [], responsibilities: [],
  started_at: now, last_active_at: now, metadata: {},
};

// The same normalized fields and spatial planner are used for live agents and simulation.
export const demoAgents: Agent[] = [
  { ...base, id: "backend", name: "Backend Engineer", role: "backend", status: "coding", task: "Implement interfaces" },
  { ...base, id: "tester", name: "Tester", role: "tester", status: "testing", parent_agent_id: "lead", current_tool: "pytest" },
  { ...base, id: "researcher", name: "Researcher", role: "researcher", status: "searching", current_tool: "rg" },
  { ...base, id: "reviewer", name: "Reviewer", role: "reviewer", status: "thinking" },
  { ...base, id: "lead", name: "Lead", role: "lead", status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id: "tester" },
  { ...base, id: "frontend", name: "Frontend Engineer", role: "frontend", status: "waiting", waiting_reason: "user_input" },
  { ...base, id: "qa-home", name: "QA Thinker", role: "qa", status: "thinking", parent_agent_id: "lead" },
  { ...base, id: "research-home", name: "Research Thinker", role: "research", status: "thinking" },
  { ...base, id: "engineer-home", name: "Engineer Thinker", role: "backend_engineer", status: "thinking" },
];

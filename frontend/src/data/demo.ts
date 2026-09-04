import type { Agent } from "../models/agent";

const now = new Date().toISOString();

export const demoAgents: Agent[] = [
  { id: "planner", name: "Planner", provider: "demo", pid: null, repository: "agent-office", worktree: null, branch: "main", status: "thinking", task: "Plan the next milestone", current_tool: null, changed_files: [], started_at: now, last_active_at: now, metadata: { role: "Product" } },
  { id: "frontend", name: "Frontend", provider: "demo", pid: null, repository: "agent-office", worktree: null, branch: "feat/office", status: "coding", task: "Build office scene", current_tool: "vite", changed_files: ["frontend/src/App.tsx"], started_at: now, last_active_at: now, metadata: { role: "UI" } },
  { id: "backend", name: "Backend", provider: "demo", pid: null, repository: "agent-office", worktree: null, branch: "feat/runtime", status: "testing", task: "Verify state engine", current_tool: "pytest", changed_files: ["backend/state/engine.py"], started_at: now, last_active_at: now, metadata: { role: "API" } },
  { id: "researcher", name: "Researcher", provider: "demo", pid: null, repository: "agent-office", worktree: null, branch: "main", status: "searching", task: "Review adapter protocols", current_tool: "search", changed_files: [], started_at: now, last_active_at: now, metadata: { role: "Research" } },
];

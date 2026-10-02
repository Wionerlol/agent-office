export const AGENT_STATES = [
  "starting",
  "thinking",
  "coding",
  "tool_running",
  "testing",
  "searching",
  "waiting",
  "idle",
  "error",
  "done",
  "offline",
] as const;

export type AgentState = (typeof AGENT_STATES)[number];

export interface Agent {
  id: string;
  name: string;
  provider: string;
  pid: number | null;
  repository: string;
  worktree: string | null;
  branch: string | null;
  status: AgentState;
  task: string | null;
  role?: string | null;
  responsibilities?: string[];
  parent_agent_id?: string | null;
  definition_id?: string | null;
  current_tool: string | null;
  changed_files: string[];
  started_at: string;
  last_active_at: string;
  metadata: Record<string, unknown>;
}

export interface AgentEvent {
  type: string;
  agent_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface ProjectInfo {
  name: string;
  path: string;
  branch?: string | null;
}

export interface CodexUsageWindow {
  used_percent: number;
  remaining_percent: number;
  window_minutes: number;
  resets_at: string;
}

export interface CodexUsage {
  status: "available" | "unavailable";
  remaining_percent: number | null;
  limiting_window: string | null;
  primary: CodexUsageWindow | null;
  secondary: CodexUsageWindow | null;
  individual: CodexUsageWindow | null;
  plan_type: string | null;
  updated_at: string | null;
}

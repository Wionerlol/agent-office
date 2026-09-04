import { AGENT_STATES, type Agent, type AgentEvent, type AgentState } from "../models/agent";
import { useAgentStore } from "../store/agents";

export type ReplayAction =
  | { at: number; kind: "event"; event: AgentEvent; sequence: number }
  | { at: number; kind: "remove"; agentId: string; sequence: number };

const isAgentState = (value: unknown): value is AgentState =>
  typeof value === "string" && AGENT_STATES.includes(value as AgentState);

export function applyHistoryEvent(event: AgentEvent): void {
  const store = useAgentStore.getState();
  if (event.type === "agent.started") {
    const agent = event.payload.agent;
    if (agent && typeof agent === "object") store.addAgent(agent as Agent);
  } else if (event.type === "agent.stopped") {
    store.setAgentStatus(event.agent_id, "offline");
  } else if (event.type === "agent.state_changed" && isAgentState(event.payload.to)) {
    store.setAgentStatus(event.agent_id, event.payload.to);
  } else if (event.type === "agent.file_changed" && typeof event.payload.file === "string") {
    const agent = store.agents[event.agent_id];
    if (agent) store.updateAgent(event.agent_id, { changed_files: [...new Set([...agent.changed_files, event.payload.file])] });
  } else if (event.type === "agent.task_updated") {
    store.updateAgent(event.agent_id, { task: typeof event.payload.task === "string" ? event.payload.task : null });
  } else if (event.type === "agent.tool_started") {
    const tool = typeof event.payload.tool === "string" ? event.payload.tool : "tool";
    const command = Array.isArray(event.payload.command) ? event.payload.command.join(" ") : String(event.payload.command ?? tool);
    const status: AgentState = tool === "test" || /pytest|(?:npm|pnpm|yarn) (?:run )?test|cargo test|go test|mvn test/i.test(command) ? "testing" : tool === "search" || /(?:^|\s)(?:rg|grep|find|fd)(?:\s|$)/.test(command) ? "searching" : "tool_running";
    store.updateAgent(event.agent_id, { current_tool: tool, status });
  } else if (event.type === "agent.tool_finished") {
    const next = isAgentState(event.payload.next_state) ? event.payload.next_state : "thinking";
    store.updateAgent(event.agent_id, { current_tool: null, status: next });
  } else if (event.type === "agent.error") {
    store.setAgentStatus(event.agent_id, "error");
  }
  store.addEvent(event);
}

export function buildReplayTimeline(events: AgentEvent[]): ReplayAction[] {
  const actions: ReplayAction[] = [];
  events.forEach((event, index) => {
    const parsed = Date.parse(event.timestamp);
    const at = Number.isNaN(parsed) ? index : parsed;
    actions.push({ at, kind: "event", event, sequence: index * 2 });
    if (event.type === "agent.stopped") {
      actions.push({ at: at + 5000, kind: "remove", agentId: event.agent_id, sequence: index * 2 + 1 });
    }
  });
  return actions.sort((left, right) => left.at - right.at || left.sequence - right.sequence);
}

export function replayDelay(actions: ReplayAction[], cursor: number, speed: number): number {
  if (cursor <= 0) return 0;
  return Math.max(0, actions[cursor].at - actions[cursor - 1].at) / speed;
}

export function applyReplayAction(action: ReplayAction): void {
  if (action.kind === "event") {
    applyHistoryEvent(action.event);
    return;
  }
  const current = useAgentStore.getState().agents[action.agentId];
  if (current?.status === "offline") useAgentStore.getState().removeAgent(action.agentId);
}

export async function loadHistory(): Promise<AgentEvent[]> {
  const response = await fetch("/api/history?limit=10000");
  if (!response.ok) throw new Error(`History request failed: ${response.status}`);
  return response.json() as Promise<AgentEvent[]>;
}

export async function restoreLiveSnapshot(): Promise<void> {
  const response = await fetch("/api/agents");
  if (!response.ok) throw new Error(`Agent request failed: ${response.status}`);
  useAgentStore.getState().replaceAgents(await response.json() as Agent[]);
}

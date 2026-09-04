import type { Agent, AgentEvent } from "../models/agent";
import { useAgentStore } from "../store/agents";

type ServerMessage =
  | { type: "snapshot"; agents: Agent[] }
  | { type: "agent.started"; agent: Agent }
  | { type: "agent.updated"; agent_id: string; changes: Partial<Agent> }
  | { type: "agent.stopped"; agent_id: string };

export function applyServerMessage(message: ServerMessage): void {
  const store = useAgentStore.getState();
  if (store.replayMode) return;
  if (message.type === "snapshot") {
    store.replaceAgents(message.agents);
    return;
  }
  if (message.type === "agent.started") {
    store.addAgent(message.agent);
    return;
  }
  if (message.type === "agent.stopped") {
    store.setAgentStatus(message.agent_id, "offline");
    window.setTimeout(() => useAgentStore.getState().removeAgent(message.agent_id), 1800);
    return;
  }
  store.updateAgent(message.agent_id, message.changes);
  const event: AgentEvent = {
    type: "agent.updated",
    agent_id: message.agent_id,
    timestamp: new Date().toISOString(),
    payload: message.changes,
  };
  store.addEvent(event);
}

function isServerMessage(value: unknown): value is ServerMessage {
  if (!value || typeof value !== "object" || !("type" in value)) return false;
  const type = (value as { type: unknown }).type;
  return typeof type === "string" && ["snapshot", "agent.started", "agent.updated", "agent.stopped"].includes(type);
}

export function connectOfficeWebSocket(url?: string): () => void {
  let stopped = false;
  let reconnectTimer: number | undefined;
  let socket: WebSocket | undefined;
  let attempt = 0;

  const connect = () => {
    if (stopped) return;
    useAgentStore.getState().setConnection(attempt ? "reconnecting" : "disconnected");
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const socketUrl = url ?? `${protocol}://${window.location.host}/ws`;
    socket = new WebSocket(socketUrl);
    socket.onopen = () => {
      attempt = 0;
      useAgentStore.getState().setConnection("connected");
    };
    socket.onmessage = (event) => {
      try {
        const message: unknown = JSON.parse(String(event.data));
        if (isServerMessage(message)) applyServerMessage(message);
      } catch (error) {
        console.warn("Ignoring invalid Agent Office message", error);
      }
    };
    socket.onerror = () => socket?.close();
    socket.onclose = () => {
      if (stopped) return;
      attempt += 1;
      useAgentStore.getState().setConnection("reconnecting");
      reconnectTimer = window.setTimeout(connect, Math.min(1000 * 2 ** attempt, 15_000));
    };
  };

  connect();
  return () => {
    stopped = true;
    if (reconnectTimer) window.clearTimeout(reconnectTimer);
    socket?.close();
    useAgentStore.getState().setConnection("disconnected");
  };
}

export async function loadProject(): Promise<void> {
  const [projectResponse, projectsResponse] = await Promise.all([
    fetch("/api/project"),
    fetch("/api/projects"),
  ]);
  if (!projectResponse.ok) throw new Error(`Project request failed: ${projectResponse.status}`);
  useAgentStore.getState().setProject(await projectResponse.json());
  if (projectsResponse.ok) useAgentStore.getState().setProjects(await projectsResponse.json());
}

export async function sendAgentEvent(
  type: string,
  agentId: string,
  payload: Record<string, unknown> = {},
): Promise<void> {
  const response = await fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      type,
      agent_id: agentId,
      timestamp: new Date().toISOString(),
      payload,
    }),
  });
  if (!response.ok) throw new Error(`Event request failed: ${response.status}`);
}

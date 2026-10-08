import { useEffect } from "react";
import type { Agent } from "../models/agent";
import { needsUser } from "../office/focus";

interface Props {
  agents: readonly Agent[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onClear: () => void;
}
export function AgentNavigator({ agents, selectedId, onSelect, onClear }: Props) {
  useEffect(() => {
    const keydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); onClear(); }
    };
    window.addEventListener("keydown", keydown);
    return () => window.removeEventListener("keydown", keydown);
  }, [onClear]);
  return <nav className="agent-navigator" aria-label="Agent navigator">
    <span className="navigator-title">Team</span>
    {agents.map((agent) => <button key={agent.id} data-agent-id={agent.id} aria-pressed={agent.id === selectedId}
      aria-label={`${agent.name}, ${agent.status}${needsUser(agent) ? ", needs you" : agent.status === "error" ? ", blocked" : ""}`}
      onClick={() => onSelect(agent.id)}>
      <span>{agent.name}</span><small>{needsUser(agent) ? "? Needs you" : agent.status === "error" ? "! Blocked" : agent.status}</small>
    </button>)}
    {!agents.length && <span className="muted">No visible agents</span>}
    <span className="sr-only" role="status">{selectedId ? `${agents.find((a) => a.id === selectedId)?.name ?? "Agent"} selected` : "Whole office"}</span>
  </nav>;
}

import type { Agent, AgentEvent } from "../models/agent";

interface AgentPanelProps {
  agent: Agent | null;
  events: AgentEvent[];
  onClose: () => void;
  visibleAgents?: readonly Agent[];
  onSelect?: (id: string) => void;
}

export function AgentPanel({ agent, events, onClose, visibleAgents = [], onSelect }: AgentPanelProps) {
  if (!agent) return <aside className="agent-panel empty-panel">Select an agent to inspect its work.</aside>;
  const agentEvents = events.filter((event) => event.agent_id === agent.id).slice(0, 5);
  const relation = (id: string) => {
    const target = visibleAgents.find((a) => a.id === id && a.id !== agent.id);
    return target && onSelect ? <button className="relation-button" onClick={() => onSelect(target.id)}>{target.name}</button>
      : <span className="muted">Not in this view</span>;
  };
  const children = visibleAgents.filter((a) => a.parent_agent_id === agent.id && a.id !== agent.id);
  return (
    <aside className="agent-panel">
      <button className="icon-button panel-close" onClick={onClose} aria-label="Close details">×</button>
      <p className="eyebrow">Agent detail</p>
      <h2>{agent.name}</h2>
      <span className={`status-pill status-${agent.status}`}>{agent.status}</span>
      <dl>
        <dt>Provider</dt><dd>{agent.provider}</dd>
        <dt>Role</dt><dd>{agent.role ?? "—"}</dd>
        <dt>Personality</dt><dd>{String(agent.metadata.personality ?? "Steady")}</dd>
        {Boolean(agent.responsibilities?.length) && <>
          <dt>Responsibilities</dt>
          <dd><ul>{agent.responsibilities?.map((item, index) => <li key={`${index}-${item}`}>{item}</li>)}</ul></dd>
        </>}
        {agent.parent_agent_id && <><dt>Parent Agent</dt><dd>{relation(agent.parent_agent_id)}</dd></>}
        {children.length > 0 && <><dt>Children</dt><dd className="relation-list">{children.map((child) => <span key={child.id}>{relation(child.id)}</span>)}</dd></>}
        {agent.definition_id && <><dt>Definition</dt><dd>{agent.definition_id}</dd></>}
        <dt>Current Task</dt><dd>{agent.task ?? "—"}</dd>
        <dt>Current State</dt><dd>{agent.status}</dd>
        {agent.waiting_reason && <><dt>Waiting reason</dt><dd>{
          agent.waiting_reason === "user_input" ? "Waiting for user input" :
          agent.waiting_reason === "child_agent" ? "Waiting for child agent" : agent.waiting_reason
        }</dd></>}
        {agent.waiting_on_agent_id && <><dt>Waiting on Agent</dt><dd>{relation(agent.waiting_on_agent_id)}</dd></>}
        <dt>PID</dt><dd>{agent.pid ?? "—"}</dd>
        <dt>Branch</dt><dd>{agent.branch ?? "—"}</dd>
        <dt>Worktree</dt><dd>{agent.worktree ?? "—"}</dd>
        <dt>Current Tool</dt><dd>{agent.current_tool ?? "—"}</dd>
        <dt>Started</dt><dd>{new Date(agent.started_at).toLocaleString()}</dd>
        <dt>Last active</dt><dd>{new Date(agent.last_active_at).toLocaleString()}</dd>
      </dl>
      <h3>Recent events</h3>
      {agentEvents.length ? <ul>{agentEvents.map((event) => <li key={`${event.timestamp}-${event.type}`}>{event.type}</li>)}</ul> : <p className="muted">No events yet.</p>}
    </aside>
  );
}

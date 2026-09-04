import { AGENT_STATES, type Agent, type AgentState } from "../models/agent";
import { sendAgentEvent } from "../api/websocket";
import { useAgentStore } from "../store/agents";

interface DebugPanelProps {
  agents: Agent[];
  enabled: boolean;
}

export function DebugPanel({ agents, enabled }: DebugPanelProps) {
  const { addAgent, removeAgent, setAgentStatus, simulationPaused, setSimulationPaused, replaceAgents, connection, project } = useAgentStore();
  if (!enabled) return null;

  const live = connection === "connected";
  const changeStatus = (agent: Agent, status: AgentState) => {
    if (live) void sendAgentEvent("agent.state_changed", agent.id, { from: agent.status, to: status });
    else setAgentStatus(agent.id, status);
  };
  const remove = (agent: Agent) => {
    if (live) void sendAgentEvent("agent.stopped", agent.id);
    else removeAgent(agent.id);
  };

  const spawn = () => {
    const sequence = agents.length + 1;
    const id = `agent-${Date.now().toString(36)}`;
    const now = new Date().toISOString();
    const agent: Agent = { id, name: `Agent ${sequence}`, provider: "debug", pid: null, repository: project?.path ?? window.location.pathname, worktree: null, branch: "main", status: "starting", task: "Debug session", current_tool: null, changed_files: [], started_at: now, last_active_at: now, metadata: { personality: "Curious" } };
    if (live) void sendAgentEvent("agent.started", id, { agent });
    else addAgent(agent);
  };
  const randomize = () => agents.forEach((agent) => changeStatus(agent, AGENT_STATES[Math.floor(Math.random() * (AGENT_STATES.length - 1))]));

  return (
    <section className="debug-panel">
      <div className="panel-heading"><div><p className="eyebrow">Simulator</p><h2>Debug controls</h2></div><button onClick={() => setSimulationPaused(!simulationPaused)}>{simulationPaused ? "Resume" : "Pause"} simulation</button></div>
      <div className="debug-actions">
        <button onClick={spawn}>Spawn agent</button>
        <button onClick={randomize}>Randomize states</button>
        <button onClick={() => agents[0] && changeStatus(agents[0], "error")}>Generate error</button>
        <button onClick={() => live ? agents.forEach(remove) : replaceAgents([])}>Reset</button>
      </div>
      <div className="debug-agents">
        {agents.map((agent) => (
          <label key={agent.id}>{agent.name}
            <select value={agent.status} onChange={(event) => changeStatus(agent, event.target.value as AgentState)}>
              {AGENT_STATES.map((state) => <option key={state}>{state}</option>)}
            </select>
            <button className="remove-button" onClick={() => remove(agent)} aria-label={`Remove ${agent.name}`}>×</button>
          </label>
        ))}
      </div>
    </section>
  );
}

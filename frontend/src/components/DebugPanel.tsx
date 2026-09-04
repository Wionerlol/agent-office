import { AGENT_STATES, type Agent, type AgentState } from "../models/agent";
import { useAgentStore } from "../store/agents";

interface DebugPanelProps {
  agents: Agent[];
  enabled: boolean;
}

export function DebugPanel({ agents, enabled }: DebugPanelProps) {
  const { addAgent, removeAgent, setAgentStatus, simulationPaused, setSimulationPaused, replaceAgents } = useAgentStore();
  if (!enabled) return null;

  const spawn = () => {
    const sequence = agents.length + 1;
    const id = `agent-${Date.now().toString(36)}`;
    const now = new Date().toISOString();
    addAgent({ id, name: `Agent ${sequence}`, provider: "debug", pid: null, repository: "agent-office", worktree: null, branch: "main", status: "starting", task: "Debug session", current_tool: null, changed_files: [], started_at: now, last_active_at: now, metadata: {} });
  };
  const randomize = () => agents.forEach((agent) => setAgentStatus(agent.id, AGENT_STATES[Math.floor(Math.random() * (AGENT_STATES.length - 1))]));

  return (
    <section className="debug-panel">
      <div className="panel-heading"><div><p className="eyebrow">Simulator</p><h2>Debug controls</h2></div><button onClick={() => setSimulationPaused(!simulationPaused)}>{simulationPaused ? "Resume" : "Pause"} simulation</button></div>
      <div className="debug-actions">
        <button onClick={spawn}>Spawn agent</button>
        <button onClick={randomize}>Randomize states</button>
        <button onClick={() => agents[0] && setAgentStatus(agents[0].id, "error")}>Generate error</button>
        <button onClick={() => replaceAgents([])}>Reset</button>
      </div>
      <div className="debug-agents">
        {agents.map((agent) => (
          <label key={agent.id}>{agent.name}
            <select value={agent.status} onChange={(event) => setAgentStatus(agent.id, event.target.value as AgentState)}>
              {AGENT_STATES.map((state) => <option key={state}>{state}</option>)}
            </select>
            <button className="remove-button" onClick={() => removeAgent(agent.id)} aria-label={`Remove ${agent.name}`}>×</button>
          </label>
        ))}
      </div>
    </section>
  );
}

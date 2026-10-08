import { useEffect, useMemo, useState } from "react";

import { connectOfficeWebSocket, loadProject } from "./api/websocket";
import { observeCodexUsage } from "./api/usage";
import { AgentPanel } from "./components/AgentPanel";
import { Achievements } from "./components/Achievements";
import { CodexUsageIndicator } from "./components/CodexUsageIndicator";
import { ProjectSelector } from "./components/ProjectSelector";
import { demoAgents } from "./data/demo";
import { useSimulation } from "./hooks/useSimulation";
import { OfficeScene } from "./office/OfficeScene";
import { useAgentStore } from "./store/agents";
import { agentsForProject } from "./store/selectors";

function App() {
  const store = useAgentStore();
  const [demoMode] = useState(() => new URLSearchParams(window.location.search).get("demo") === "true");
  const allAgents = useMemo(() => Object.values(store.agents), [store.agents]);
  const agents = useMemo(
    () => agentsForProject(allAgents, store.selectedProjectPath),
    [allAgents, store.selectedProjectPath],
  );
  const selected = store.selectedAgentId ? store.agents[store.selectedAgentId] ?? null : null;

  useEffect(() => {
    if (demoMode && Object.keys(useAgentStore.getState().agents).length === 0) {
      useAgentStore.getState().replaceAgents(demoAgents);
      useAgentStore.getState().setConnection("simulation");
    }
    if (!demoMode) {
      void loadProject().catch(() => undefined);
      const disconnect = connectOfficeWebSocket();
      const stopUsageObserver = observeCodexUsage();
      return () => {
        disconnect();
        stopUsageObserver();
      };
    }
  }, [demoMode]);
  useSimulation(demoMode);

  return (
    <main>
      <header className="topbar">
        <div><p className="eyebrow">{store.project?.name ?? "Local runtime observatory"}</p><h1>Agent Office</h1></div>
        <div className="header-actions">
          <ProjectSelector />
          <CodexUsageIndicator usage={store.codexUsage} />
          <span className={`connection connection-${store.connection}`}><i />{store.connection}</span>
          <span className="agent-count">{agents.length} agents</span>
          {demoMode && <button onClick={() => store.setSimulationPaused(!store.simulationPaused)}>
            {store.simulationPaused ? "Resume" : "Pause"} simulation
          </button>}
        </div>
      </header>
      <Achievements agents={agents} />
      <section className="workspace">
        <div className="scene-column">
          <OfficeScene agents={agents} deskCount={store.deskCount} usage={store.codexUsage} />
        </div>
        <AgentPanel agent={selected} events={store.recentEvents} onClose={() => store.selectAgent(null)} />
      </section>
    </main>
  );
}

export default App;

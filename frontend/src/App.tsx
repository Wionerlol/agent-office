import { useEffect, useMemo, useState } from "react";

import { AgentPanel } from "./components/AgentPanel";
import { DebugPanel } from "./components/DebugPanel";
import { demoAgents } from "./data/demo";
import { useSimulation } from "./hooks/useSimulation";
import { OfficeScene } from "./office/OfficeScene";
import { useAgentStore } from "./store/agents";

function App() {
  const store = useAgentStore();
  const [debugOpen, setDebugOpen] = useState(true);
  const [demoMode] = useState(() => new URLSearchParams(window.location.search).get("demo") !== "false");
  const agents = useMemo(() => Object.values(store.agents), [store.agents]);
  const selected = store.selectedAgentId ? store.agents[store.selectedAgentId] ?? null : null;

  useEffect(() => {
    if (demoMode && Object.keys(useAgentStore.getState().agents).length === 0) {
      useAgentStore.getState().replaceAgents(demoAgents);
      useAgentStore.getState().setConnection("simulation");
    }
  }, [demoMode]);
  useSimulation(demoMode);

  return (
    <main>
      <header className="topbar">
        <div><p className="eyebrow">Local runtime observatory</p><h1>Agent Office</h1></div>
        <div className="header-actions">
          <span className={`connection connection-${store.connection}`}><i />{store.connection}</span>
          <span className="agent-count">{agents.length} agents</span>
          <button onClick={() => setDebugOpen((value) => !value)}>{debugOpen ? "Hide" : "Show"} debug</button>
        </div>
      </header>
      <section className="workspace">
        <div className="scene-column">
          <OfficeScene agents={agents} />
          <DebugPanel agents={agents} enabled={debugOpen} />
        </div>
        <AgentPanel agent={selected} events={store.recentEvents} onClose={() => store.selectAgent(null)} />
      </section>
    </main>
  );
}

export default App;

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { connectOfficeWebSocket, loadProject } from "./api/websocket";
import { observeCodexUsage } from "./api/usage";
import { AgentNavigator } from "./components/AgentNavigator";
import { useReducedMotion } from "./hooks/useReducedMotion";
import { AgentPanel } from "./components/AgentPanel";
import { Achievements } from "./components/Achievements";
import { CodexUsageIndicator } from "./components/CodexUsageIndicator";
import { ProjectSelector } from "./components/ProjectSelector";
import { demoAgents } from "./data/demo";
import { useInteractionCleanup } from "./hooks/useInteractionCleanup";
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
  const selected = agents.find((agent) => agent.id === store.selectedAgentId) ?? null;
  const reducedMotion = useReducedMotion();
  const sceneColumnRef = useRef<HTMLDivElement>(null);
  const clearSelection = useCallback(() => {
    sceneColumnRef.current?.querySelector<HTMLButtonElement>('button[aria-pressed="true"]')?.focus();
    useAgentStore.getState().selectAgent(null);
  }, []);

  const selectRelated = useCallback((id: string) => {
    const buttons = sceneColumnRef.current?.querySelectorAll<HTMLButtonElement>("button[data-agent-id]");
    Array.from(buttons ?? []).find((button) => button.dataset.agentId === id)?.focus();
    useAgentStore.getState().selectAgent(id);
  }, []);

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
  useInteractionCleanup();

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
        <div className="scene-column" ref={sceneColumnRef}>
          <AgentNavigator agents={agents} selectedId={selected?.id ?? null} onSelect={store.selectAgent} onClear={clearSelection} />
          <OfficeScene agents={agents} deskCount={store.deskCount} usage={store.codexUsage} cues={store.interactionCues} selectedId={selected?.id ?? null} reducedMotion={reducedMotion} />
          <p className="interaction-legend">? Needs you · ↔ Child wait · → Delegated · ✓ Complete · ! Blocked</p>
        </div>
        <AgentPanel agent={selected} visibleAgents={agents} onSelect={selectRelated} events={store.recentEvents} onClose={clearSelection} />
      </section>
    </main>
  );
}

export default App;

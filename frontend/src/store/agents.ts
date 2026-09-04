import { create } from "zustand";

import type { Agent, AgentEvent, AgentState, ProjectInfo } from "../models/agent";

export type ConnectionState = "connected" | "reconnecting" | "disconnected" | "simulation" | "replay";

interface AgentStore {
  agents: Record<string, Agent>;
  selectedAgentId: string | null;
  recentEvents: AgentEvent[];
  project: ProjectInfo | null;
  projects: ProjectInfo[];
  selectedProjectPath: string | null;
  connection: ConnectionState;
  simulationPaused: boolean;
  replayMode: boolean;
  addAgent: (agent: Agent) => void;
  removeAgent: (id: string) => void;
  updateAgent: (id: string, changes: Partial<Agent>) => void;
  setAgentStatus: (id: string, status: AgentState) => void;
  replaceAgents: (agents: Agent[]) => void;
  selectAgent: (id: string | null) => void;
  addEvent: (event: AgentEvent) => void;
  setProject: (project: ProjectInfo | null) => void;
  setProjects: (projects: ProjectInfo[]) => void;
  selectProject: (path: string | null) => void;
  setConnection: (connection: ConnectionState) => void;
  setSimulationPaused: (paused: boolean) => void;
  setReplayMode: (enabled: boolean) => void;
  reset: () => void;
}

const initialState = {
  agents: {},
  selectedAgentId: null,
  recentEvents: [],
  project: null,
  projects: [],
  selectedProjectPath: null,
  connection: "disconnected" as ConnectionState,
  simulationPaused: false,
  replayMode: false,
};

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,
  addAgent: (agent) => set((state) => ({ agents: { ...state.agents, [agent.id]: agent } })),
  removeAgent: (id) =>
    set((state) => {
      const agents = { ...state.agents };
      delete agents[id];
      return {
        agents,
        selectedAgentId: state.selectedAgentId === id ? null : state.selectedAgentId,
      };
    }),
  updateAgent: (id, changes) =>
    set((state) => {
      const current = state.agents[id];
      if (!current) return state;
      return { agents: { ...state.agents, [id]: { ...current, ...changes } } };
    }),
  setAgentStatus: (id, status) =>
    set((state) => {
      const current = state.agents[id];
      if (!current) return state;
      return {
        agents: {
          ...state.agents,
          [id]: { ...current, status, last_active_at: new Date().toISOString() },
        },
      };
    }),
  replaceAgents: (agents) =>
    set({ agents: Object.fromEntries(agents.map((agent) => [agent.id, agent])) }),
  selectAgent: (selectedAgentId) => set({ selectedAgentId }),
  addEvent: (event) =>
    set((state) => ({ recentEvents: [event, ...state.recentEvents].slice(0, 100) })),
  setProject: (project) => set((state) => ({
    project,
    selectedProjectPath: state.selectedProjectPath ?? project?.path ?? null,
  })),
  setProjects: (projects) => set({ projects }),
  selectProject: (selectedProjectPath) => set({ selectedProjectPath }),
  setConnection: (connection) => set({ connection }),
  setSimulationPaused: (simulationPaused) => set({ simulationPaused }),
  setReplayMode: (replayMode) => set({ replayMode, connection: replayMode ? "replay" : "connected" }),
  reset: () => set(initialState),
}));

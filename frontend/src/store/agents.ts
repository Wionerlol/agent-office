import { create } from "zustand";

import type { Agent, AgentEvent, AgentState, CodexUsage, ProjectInfo, ServerMessage } from "../models/agent";

import { CUE_TTL, MAX_CUES, MAX_START_KEYS, OFFLINE_GRACE, liveCues, startKey, type InteractionCue, type InteractionKind } from "../models/interaction";

export type ConnectionState = "connected" | "reconnecting" | "disconnected" | "simulation";

interface AgentStore {
  agents: Record<string, Agent>;
  selectedAgentId: string | null;
  recentEvents: AgentEvent[];
  interactionCues: InteractionCue[];
  knownStarts: string[];
  cueSequence: number;
  offlineUntil: Record<string, number>;
  receiveMessage: (message: ServerMessage, now?: number) => void;
  sweepInteractions: (now?: number) => void;
  project: ProjectInfo | null;
  projects: ProjectInfo[];
  selectedProjectPath: string | null;
  connection: ConnectionState;
  simulationPaused: boolean;
  deskCount: number;
  codexUsage: CodexUsage | null;
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
  setDeskCount: (count: number) => void;
  setCodexUsage: (usage: CodexUsage) => void;
  reset: () => void;
}

const initialState = {
  agents: {},
  selectedAgentId: null,
  recentEvents: [],
  interactionCues: [],
  knownStarts: [],
  cueSequence: 0,
  offlineUntil: {},
  project: null,
  projects: [],
  selectedProjectPath: null,
  connection: "disconnected" as ConnectionState,
  simulationPaused: false,
  deskCount: 8,
  codexUsage: null,
};

export const useAgentStore = create<AgentStore>((set) => ({
  ...initialState,
  receiveMessage: (message, now = Date.now()) => set((state) => {
    if (message.type === "snapshot") return {
      agents: Object.fromEntries(message.agents.map((a) => [a.id, a])),
      interactionCues: [],
      knownStarts: [...new Set([...state.knownStarts, ...message.agents.map(startKey)])].slice(-MAX_START_KEYS),
      offlineUntil: Object.fromEntries(message.agents.filter((a) => a.status === "offline").map((a) => [a.id, now + OFFLINE_GRACE])),
    };
    const agents = { ...state.agents }, offlineUntil = { ...state.offlineUntil };
    let cues = liveCues(state.interactionCues, agents, now), knownStarts = state.knownStarts;
    let sequence = state.cueSequence;
    const cue = (kind: InteractionKind, sourceAgentId: string, targetAgentId?: string) => {
      cues = [...cues, { id: `cue-${++sequence}`, kind, sourceAgentId, targetAgentId,
        createdAt: now, expiresAt: now + CUE_TTL[kind] }].slice(-MAX_CUES);
    };
    const parentVisible = (a: Agent) => a.parent_agent_id && a.parent_agent_id !== a.id
      && agents[a.parent_agent_id] && agents[a.parent_agent_id].status !== "offline";
    if (message.type === "agent.started") {
      const agent = message.agent, previous = agents[agent.id];
      const key = startKey(agent);
      if (previous && previous.started_at !== agent.started_at) {
        cues = cues.filter((c) => c.sourceAgentId !== agent.id && c.targetAgentId !== agent.id);
      }
      agents[agent.id] = agent;
      delete offlineUntil[agent.id];
      if (!knownStarts.includes(key) && (!previous || previous.started_at !== agent.started_at)
        && agent.status !== "offline" && parentVisible(agent)) cue("delegation", agent.parent_agent_id!, agent.id);
      knownStarts = [...new Set([...knownStarts, key])].slice(-MAX_START_KEYS);
    } else if (message.type === "agent.stopped") {
      if (!agents[message.agent_id]) return state;
      agents[message.agent_id] = { ...agents[message.agent_id], status: "offline" };
      offlineUntil[message.agent_id] ??= now + OFFLINE_GRACE;
    } else {
      const previous = agents[message.agent_id];
      if (!previous) return state;
      const agent = { ...previous, ...message.changes, id: previous.id };
      agents[agent.id] = agent;
      if (agent.status !== "offline") delete offlineUntil[agent.id];
      if (previous.status !== "done" && agent.status === "done" && parentVisible(agent)) cue("handoff", agent.id, agent.parent_agent_id!);
      if (previous.status !== "error" && agent.status === "error") cue("blocked", agent.id);
    }
    return { agents, offlineUntil, knownStarts, cueSequence: sequence, interactionCues: liveCues(cues, agents, now) };
  }),
  sweepInteractions: (now = Date.now()) => set((state) => {
    const expired = Object.entries(state.offlineUntil).filter(([, deadline]) => deadline <= now);
    const agents = expired.length ? { ...state.agents } : state.agents;
    const offlineUntil = expired.length ? { ...state.offlineUntil } : state.offlineUntil;
    for (const [id] of expired) {
      if (agents[id]?.status === "offline") delete agents[id];
      delete offlineUntil[id];
    }
    const interactionCues = liveCues(state.interactionCues, agents, now);
    if (!expired.length && interactionCues.length === state.interactionCues.length) return state;
    return { agents, offlineUntil, interactionCues,
      selectedAgentId: state.selectedAgentId && !agents[state.selectedAgentId] ? null : state.selectedAgentId };
  }),
  addAgent: (agent) => set((state) => ({ agents: { ...state.agents, [agent.id]: agent } })),
  removeAgent: (id) =>
    set((state) => {
      const agents = { ...state.agents };
      delete agents[id];
      return {
        agents,
        interactionCues: state.interactionCues.filter((c) => c.sourceAgentId !== id && c.targetAgentId !== id),
        offlineUntil: Object.fromEntries(Object.entries(state.offlineUntil).filter(([key]) => key !== id)),
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
    set({ agents: Object.fromEntries(agents.map((agent) => [agent.id, agent])), interactionCues: [], offlineUntil: {} }),
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
  setDeskCount: (deskCount) => set({ deskCount }),
  setCodexUsage: (codexUsage) => set({ codexUsage }),
  reset: () => set(initialState),
}));

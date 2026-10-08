import type { Agent } from "./agent";

export type InteractionKind = "delegation" | "handoff" | "blocked";
export interface InteractionCue {
  id: string;
  kind: InteractionKind;
  sourceAgentId: string;
  targetAgentId?: string;
  createdAt: number;
  expiresAt: number;
}
export const CUE_TTL: Readonly<Record<InteractionKind, number>> = {
  delegation: 3000, handoff: 3000, blocked: 4000,
};
export const MAX_CUES = 48;
export const MAX_START_KEYS = 128;
export const OFFLINE_GRACE = 5000;
export const INTERACTION_SWEEP_MS = 250;

export interface CoordinationLink { sourceAgentId: string; targetAgentId: string }

/** Only current explicit waits between rendered agents have persistent edges. */
export function coordinationLinks(agents: readonly Agent[]): CoordinationLink[] {
  const visible = new Map(agents.filter((a) => a.status !== "offline").map((a) => [a.id, a]));
  return agents.flatMap((a) => a.status === "waiting" && a.waiting_reason === "child_agent"
    && a.waiting_on_agent_id && a.waiting_on_agent_id !== a.id && visible.has(a.waiting_on_agent_id)
    ? [{ sourceAgentId: a.id, targetAgentId: a.waiting_on_agent_id }] : []);
}

export const startKey = (agent: Agent): string => JSON.stringify([agent.id, agent.started_at]);
export function liveCues(cues: readonly InteractionCue[], agents: Record<string, Agent>, now: number): InteractionCue[] {
  const live = (id: string) => agents[id] && agents[id].status !== "offline";
  return cues.filter((cue) => cue.expiresAt > now && live(cue.sourceAgentId)
    && (!cue.targetAgentId || live(cue.targetAgentId))).slice(-MAX_CUES);
}

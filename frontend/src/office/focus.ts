import type { Agent } from "../models/agent";
import type { InteractionCue } from "../models/interaction";

export type RelationKind = "parent" | "child" | "waiting_on" | "waiting_for_me" | "interaction";
export interface AgentFocus {
  selected: boolean;
  related: boolean;
  dimmed: boolean;
  priority: number;
  importantLabel: boolean;
  expandedLabel: boolean;
  relationshipKinds: RelationKind[];
}
export const needsUser = (agent: Agent): boolean => agent.status === "waiting" && agent.waiting_reason === "user_input";
const waitTarget = (agent: Agent): string | null => agent.status === "waiting"
  && agent.waiting_reason === "child_agent" ? agent.waiting_on_agent_id ?? null : null;

/** Presentation only. Inputs must be the currently rendered project subset. */
export function focusFor(agents: readonly Agent[], selectedId: string | null, hoveredId: string | null,
  cues: readonly InteractionCue[] = [], now = 0): Map<string, AgentFocus> {
  const selected = agents.find((a) => a.id === selectedId);
  const waitingEndpoints = new Set<string>();
  const visible = new Set(agents.filter((a) => a.status !== "offline").map((a) => a.id));
  for (const agent of agents) {
    const target = waitTarget(agent);
    if (target && target !== agent.id && visible.has(target)) {
      waitingEndpoints.add(agent.id); waitingEndpoints.add(target);
    }
  }
  return new Map(agents.map((agent) => {
    const kinds: RelationKind[] = [];
    const isSelected = agent.id === selected?.id;
    if (selected && !isSelected) {
      if (selected.parent_agent_id === agent.id) kinds.push("parent");
      if (agent.parent_agent_id === selected.id) kinds.push("child");
      if (waitTarget(selected) === agent.id) kinds.push("waiting_on");
      if (waitTarget(agent) === selected.id) kinds.push("waiting_for_me");
      if (cues.some((c) => c.createdAt <= now && c.expiresAt > now
        && ((c.sourceAgentId === selected.id && c.targetAgentId === agent.id)
          || (c.targetAgentId === selected.id && c.sourceAgentId === agent.id)))) kinds.push("interaction");
    }
    const hovered = agent.id === hoveredId;
    const priority = needsUser(agent) ? 6 : isSelected ? 5 : agent.status === "error" ? 4
      : hovered ? 3 : waitingEndpoints.has(agent.id) ? 2 : 1;
    return [agent.id, { selected: isSelected, related: kinds.length > 0,
      dimmed: Boolean(selected && !isSelected && !kinds.length && !needsUser(agent) && agent.status !== "error" && !hovered),
      priority, importantLabel: priority >= 2, expandedLabel: isSelected || hovered, relationshipKinds: kinds }];
  }));
}

export function connectorEmphasis(source: string, target: string, selectedId: string | null,
  focus: ReadonlyMap<string, AgentFocus>): "normal" | "focused" | "quiet" {
  if (!selectedId || !focus.get(selectedId)?.selected) return "normal";
  return source === selectedId || target === selectedId ? "focused" : "quiet";
}

export function identitySummary(agent: Agent): string {
  return [agent.role, agent.status.toUpperCase()].filter(Boolean).join(" / ");
}

export function officeDescription(agents: readonly Agent[], selectedId: string | null): string {
  const selected = agents.find((a) => a.id === selectedId);
  const summary = `Live agent office map. ${agents.length} agents. ${agents.filter(needsUser).length} need you. ${agents.filter((a) => a.status === "error").length} blocked. Use the agent navigator to inspect.`;
  if (!selected) return summary;
  const parent = agents.find((a) => a.id === selected.parent_agent_id);
  const target = agents.find((a) => a.id === waitTarget(selected));
  const waiting = agents.filter((a) => waitTarget(a) === selected.id).slice(0, 3);
  return [summary, `${selected.name}: ${selected.status}${needsUser(selected) ? ", ? Needs you" : ""}.`,
    parent ? `Parent: ${parent.name}.` : "", target ? `Waiting on ${target.name}.` : "",
    ...waiting.map((a) => `${a.name} waiting on ${selected.name}.`)].filter(Boolean).join(" ");
}

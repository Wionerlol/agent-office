import type { Agent, AgentState } from "../models/agent";

export type VisualState =
  | "entering"
  | "thinking"
  | "typing"
  | "reading"
  | "working_machine"
  | "testing"
  | "waiting"
  | "user_attention"
  | "coordinating"
  | "drinking"
  | "error"
  | "celebration"
  | "leaving";

export interface AgentVisual {
  zone: string;
  animation: VisualState;
}

export function visualFor(state: AgentState, deskId: string): AgentVisual {
  const desk = { zone: deskId, animation: "thinking" as const };
  const mapping: Record<AgentState, AgentVisual> = {
    starting: { zone: "entrance", animation: "entering" },
    thinking: desk,
    coding: { zone: deskId, animation: "typing" },
    searching: { zone: "library", animation: "reading" },
    tool_running: { zone: "tool_lab", animation: "working_machine" },
    testing: { zone: "test_lab", animation: "testing" },
    waiting: { zone: "lounge", animation: "waiting" },
    idle: { zone: "coffee_area", animation: "drinking" },
    error: { zone: deskId, animation: "error" },
    done: { zone: deskId, animation: "celebration" },
    offline: { zone: "exit", animation: "leaving" },
  };
  return mapping[state];
}

export type HomeZone = "desk" | "test_lab" | "library" | "review_area";
export type SpatialAgent = Pick<Agent, "id" | "role" | "status" | "waiting_reason" | "waiting_on_agent_id">;

export interface SpatialBehavior {
  homeZone: HomeZone;
  destinationZone: string;
  animation: VisualState;
  attention: "user" | "child" | null;
  indicator: string | null;
  holdPosition: boolean;
}

const ROLE_HOMES: Readonly<Record<string, HomeZone>> = {
  tester: "test_lab", testing: "test_lab", qa: "test_lab",
  research: "library", researcher: "library",
  reviewer: "review_area", code_review: "review_area", review: "review_area",
  backend: "desk", backend_engineer: "desk",
  frontend: "desk", frontend_engineer: "desk",
  lead: "desk", leader: "desk", coordinator: "desk",
};

export function homeZoneFor(role: Agent["role"]): HomeZone {
  const normalized = role?.trim().toLowerCase() ?? "";
  return Object.hasOwn(ROLE_HOMES, normalized) ? ROLE_HOMES[normalized] : "desk";
}

/** Visual interpretation only: lifecycle > attention > explicit child wait > work > home. */
export function spatialBehaviorFor(agent: SpatialAgent, deskId: string): SpatialBehavior {
  const homeZone = homeZoneFor(agent.role);
  const home = homeZone === "desk" ? deskId : homeZone;
  const legacy = visualFor(agent.status, deskId);
  const plan: SpatialBehavior = {
    homeZone, destinationZone: legacy.zone, animation: legacy.animation,
    attention: null, indicator: null, holdPosition: false,
  };
  // Terminal celebration starts immediately, rather than spending the grace period walking.
  if (agent.status === "done") return { ...plan, destinationZone: home, indicator: "✓ Done", holdPosition: true };
  if (["starting", "offline", "error"].includes(agent.status)) return plan;
  if (agent.status === "waiting" && agent.waiting_reason === "user_input") {
    return { ...plan, destinationZone: "user_attention", animation: "user_attention", attention: "user", indicator: "? Needs you" };
  }
  if (agent.status === "waiting" && agent.waiting_reason === "child_agent"
    && agent.waiting_on_agent_id?.trim() && agent.waiting_on_agent_id !== agent.id) {
    return { ...plan, destinationZone: "coordination", animation: "coordinating", attention: "child", indicator: "↔ Child wait" };
  }
  if (agent.status === "thinking" || agent.status === "idle") {
    return { ...plan, destinationZone: home, animation: agent.status === "idle" ? "waiting" : "thinking" };
  }
  return plan;
}

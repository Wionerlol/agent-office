import type { AgentState } from "../models/agent";

export type VisualState =
  | "entering"
  | "thinking"
  | "typing"
  | "reading"
  | "working_machine"
  | "testing"
  | "waiting"
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

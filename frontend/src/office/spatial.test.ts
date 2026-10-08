import { describe, expect, it } from "vitest";
import { AGENT_STATES } from "../models/agent";
import { demoAgents } from "../data/demo";
import { homeZoneFor, spatialBehaviorFor, type SpatialAgent } from "./visual";
import { POSITIONS, StableZoneSlots } from "./layout";
import { isOfficePositionWalkable, routeBetween } from "./navigation";

const agent = (changes: Partial<SpatialAgent> = {}): SpatialAgent => ({ id: "one", status: "thinking", role: null, ...changes });
const plan = (changes: Partial<SpatialAgent> = {}) => spatialBehaviorFor(agent(changes), "desk-3");

describe("semantic spatial behavior", () => {
  it.each([
    ["tester", "test_lab"], ["testing", "test_lab"], [" QA ", "test_lab"],
    ["researcher", "library"], ["research", "library"],
    ["reviewer", "review_area"], ["code_review", "review_area"], ["review", "review_area"],
    ["backend", "desk-3"], ["backend_engineer", "desk-3"], ["frontend", "desk-3"], ["frontend_engineer", "desk-3"],
    ["lead", "desk-3"], ["leader", "desk-3"], ["coordinator", "desk-3"],
    ["security tester", "desk-3"], ["toString", "desk-3"], ["__proto__", "desk-3"], [null, "desk-3"], ["", "desk-3"],
  ])("maps exact alias %s for thinking and idle", (role, destinationZone) => {
    for (const status of ["thinking", "idle"] as const) expect(plan({ role, status }).destinationZone).toBe(destinationZone);
  });
  it.each([
    ["backend", "testing", "test_lab"], ["tester", "searching", "library"],
    ["researcher", "coding", "desk-3"], ["researcher", "tool_running", "tool_lab"],
  ] as const)("%s + %s follows work", (role, status, zone) => {
    expect(plan({ role, status }).destinationZone).toBe(zone);
    expect(plan({ role, status }).homeZone).toBe(homeZoneFor(role));
  });
  it("uses explicit WAITING/user_input before role and child context", () => {
    for (const role of ["tester", "reviewer", "arbitrary", null]) {
      expect(plan({ role, status: "waiting", waiting_reason: "user_input", waiting_on_agent_id: "child" })).toMatchObject({ destinationZone: "user_attention", attention: "user", indicator: "? Needs you" });
    }
    expect(plan({ status: "testing", waiting_reason: "user_input" }).destinationZone).toBe("test_lab");
  });
  it("requires a deterministic non-self child reference", () => {
    expect(plan({ status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id: "child" })).toMatchObject({ destinationZone: "coordination", animation: "coordinating", attention: "child" });
    for (const waiting_on_agent_id of [undefined, null, "", " ", "one"]) expect(plan({ status: "waiting", waiting_reason: "child_agent", waiting_on_agent_id }).destinationZone).toBe("lounge");
    expect(plan({ status: "waiting", waiting_on_agent_id: "child" }).destinationZone).toBe("lounge");
    expect(plan({ status: "thinking", waiting_reason: "child_agent", waiting_on_agent_id: "child" }).destinationZone).toBe("desk-3");
  });
  it("lifecycle outranks stale context and celebration does not require a trip", () => {
    expect(plan({ status: "starting", waiting_reason: "user_input" })).toMatchObject({ destinationZone: "entrance", animation: "entering" });
    expect(plan({ status: "offline" })).toMatchObject({ destinationZone: "exit", animation: "leaving" });
    expect(plan({ role: "tester", status: "done" })).toMatchObject({ animation: "celebration", holdPosition: true, indicator: "✓ Done" });
    expect(plan({ status: "error", waiting_reason: "user_input" })).toMatchObject({ destinationZone: "desk-3", animation: "error" });
  });
  it("is pure and deterministic for all normalized states and unknown roles", () => {
    for (const status of AGENT_STATES) {
      const input = Object.freeze(agent({ role: "unknown custom role", status }));
      expect(spatialBehaviorFor(input, "desk-3")).toEqual(spatialBehaviorFor({ ...input }, "desk-3"));
      expect(spatialBehaviorFor(input, "desk-3").homeZone).toBe("desk");
    }
  });
  it("simulation uses normalized semantic and parent fields", () => {
    const byId = Object.fromEntries(demoAgents.map((a) => [a.id, a]));
    expect(byId.tester.parent_agent_id).toBe(byId.lead.id);
    expect(spatialBehaviorFor(byId.lead, "desk-1").attention).toBe("child");
    expect(spatialBehaviorFor(byId.frontend, "desk-1").attention).toBe("user");
    expect(spatialBehaviorFor(byId.reviewer, "desk-1").destinationZone).toBe("review_area");
  });
});

describe("stable spatial slots", () => {
  it("adding/removing/reordering peers and returning home never compact existing seats", () => {
    const slots = new StableZoneSlots();
    const a = { id: "zeta", zone: "test_lab" }, b = { id: "alpha", zone: "test_lab" };
    const original = slots.place([a]).get(a.id), pair = slots.place([b, a]);
    expect(pair.get(a.id)).toEqual(original);
    expect(slots.place([a, b])).toEqual(pair);
    expect(slots.place([a, { ...b, zone: "library" }]).get(a.id)).toEqual(original);
    expect(slots.place([b, a]).get(a.id)).toEqual(original);
    expect(slots.place([a, { id: "other", zone: "desk-1" }]).get(a.id)).toEqual(original);
  });
  it.each(["test_lab", "library", "review_area", "user_attention", "lounge", "coordination", "tool_lab", "desk-1"])("%s has unique walkable reachable seats even when crowded", (zone) => {
    for (const count of [1, 2, 3, 8]) {
      const positions = new StableZoneSlots().place(Array.from({ length: count }, (_, i) => ({ id: `agent-${i}`, zone })));
      expect(new Set([...positions.values()].map((p) => `${p.x},${p.y}`)).size).toBe(count);
      for (const point of positions.values()) {
        expect(isOfficePositionWalkable(point), `${zone}: ${point.x},${point.y}`).toBe(true);
        expect(routeBetween(POSITIONS.entrance, point).length, zone).toBeGreaterThan(0);
      }
    }
  });
  it("generic waiting and coordination share floor reservations", () => {
    const positions = new StableZoneSlots().place([{ id: "parent", zone: "coordination" }, { id: "generic", zone: "lounge" }]);
    expect(positions.get("parent")).not.toEqual(positions.get("generic"));
  });
  it("prunes exited agents and resets fully empty rooms", () => {
    const slots = new StableZoneSlots(), first = slots.place([{ id: "old", zone: "library" }]).get("old");
    slots.place([]);
    expect(slots.place([{ id: "new", zone: "library" }]).get("new")).toEqual(first);
    slots.clear();
    expect(slots.place([{ id: "new", zone: "library" }]).get("new")).toEqual(first);
  });
});

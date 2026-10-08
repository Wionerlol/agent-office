import { describe, expect, it } from "vitest";
import { demoAgents } from "../data/demo";
import { connectorEmphasis, focusFor, identitySummary, officeDescription } from "./focus";
import { placeLabels } from "./readability";
import { bodyPose } from "./motion";
import { StableZoneSlots } from "./layout";

const tester = demoAgents[1], lead = demoAgents[4];
describe("frontend focus and readability policy", () => {
  it("uses direct explicit relationships, never repository/task/role peers", () => {
    const sibling = { ...tester, id: "sibling" };
    const peer = { ...tester, id: "peer", parent_agent_id: null };
    const projection = focusFor([tester, lead, sibling, peer], tester.id, null);
    expect(projection.get(tester.id)).toMatchObject({ selected: true, dimmed: false });
    expect(projection.get(lead.id)?.relationshipKinds).toEqual(["parent", "waiting_for_me"]);
    expect(projection.get(sibling.id)).toMatchObject({ related: false, dimmed: true });
    expect(projection.get(peer.id)).toMatchObject({ related: false, dimmed: true });
    const parentFocus = focusFor([tester, lead], lead.id, null);
    expect(parentFocus.get(tester.id)?.relationshipKinds).toEqual(["child", "waiting_on"]);
  });
  it("only active visible transient endpoints supply context", () => {
    const cue = { id: "one", kind: "delegation" as const, sourceAgentId: "backend", targetAgentId: "tester", createdAt: 10, expiresAt: 30 };
    expect(focusFor(demoAgents, "backend", null, [cue], 20).get("tester")?.related).toBe(true);
    expect(focusFor(demoAgents, "backend", null, [cue], 30).get("tester")?.related).toBe(false);
    expect(focusFor([tester], "backend", null, [cue], 20).get("tester")?.dimmed).toBe(false);
  });
  it("orders attention, selected, error, hover, wait endpoints and ordinary labels", () => {
    const team = [...demoAgents, { ...tester, id: "error", status: "error" as const }];
    const focus = focusFor(team, "backend", "researcher");
    expect(["frontend", "backend", "error", "researcher", "tester", "reviewer"].map((id) => focus.get(id)?.priority)).toEqual([6, 5, 4, 3, 2, 1]);
    expect(focus.get("frontend")).toMatchObject({ dimmed: false, importantLabel: true });
    expect(focus.get("error")).toMatchObject({ dimmed: false, importantLabel: true });
    expect(identitySummary({ ...tester, task: "private", current_tool: "sh private-command" })).toBe("tester / TESTING");
  });
  it("emphasizes only selected endpoint connectors and restores whole-office emphasis", () => {
    const focus = focusFor(demoAgents, tester.id, null);
    expect(connectorEmphasis("lead", "tester", tester.id, focus)).toBe("focused");
    expect(connectorEmphasis("backend", "researcher", tester.id, focus)).toBe("quiet");
    expect(connectorEmphasis("lead", "tester", null, focus)).toBe("normal");
  });
  it("gives crowded important labels first choice without changing physical slots", () => {
    const slots = new StableZoneSlots();
    const occupants = Array.from({ length: 8 }, (_, i) => ({ id: `a${i}`, zone: "test_lab" }));
    const before = slots.place(occupants);
    const labels = placeLabels([1, 6, 5, 4].map((priority, i) => ({ id: `a${i}`, priority, x: 900, y: 400, width: 130, height: 36, eligible: true })));
    expect(labels.has("a0")).toBe(false);
    expect(["a1", "a2", "a3"].map((id) => labels.has(id))).toEqual([true, true, true]);
    expect(new Set([...labels.values()].map((p) => JSON.stringify(p))).size).toBe(3);
    expect(slots.place(occupants)).toEqual(before);
    expect(placeLabels([...occupants].map(({ id }) => ({ id, x: 900, y: 400, width: 100, height: 36, priority: 1, eligible: false })))).toEqual(new Map());
  });
  it("keeps a concise accessible summary and selected explicit context", () => {
    expect(officeDescription(demoAgents, "tester")).toContain("Parent: Lead.");
    expect(officeDescription(demoAgents, "tester")).toContain("Lead waiting on Tester.");
    expect(officeDescription(demoAgents, null)).not.toContain("Implement interfaces");
    const hundred = Array.from({ length: 100 }, (_, i) => ({ ...tester, id: `${i}` }));
    expect(officeDescription(hundred, null).length).toBeLessThan(200);
  });
  it("reduced motion removes decoration while retaining static body/attention", () => {
    for (const animation of ["typing", "celebration", "error", "user_attention"] as const) {
      expect(bodyPose(animation, 1, true)).toEqual({ y: 0, rotation: 0, alpha: 1, attentionAlpha: 1 });
    }
    expect(bodyPose("typing", 1, false).y).not.toBe(0);
  });
});

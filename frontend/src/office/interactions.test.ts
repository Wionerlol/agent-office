import { describe, expect, it, vi } from "vitest";
import { focusFor } from "./focus";
import { Container } from "pixi.js";
import { demoAgents } from "../data/demo";
import type { InteractionCue } from "../models/interaction";
import { InteractionLayer, interactionFrame, interactionDescription } from "./interactions";

vi.mock("pixi.js", async () => {
  const context = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  const actual = await vi.importActual<typeof import("pixi.js")>("pixi.js");
  context.mockRestore();
  return actual;
});

const parent = { ...demoAgents[4], waiting_on_agent_id: "child" };
const child = { ...demoAgents[1], id: "child", status: "testing" as const };
const positions = new Map([[parent.id, { x: 200, y: 300, scale: 1 }], [child.id, { x: 800, y: 400, scale: 1 }]]);
const cue: InteractionCue = { id: "one", kind: "handoff", sourceAgentId: child.id, targetAgentId: parent.id, createdAt: 0, expiresAt: 3000 };

describe("interaction projection/rendering", () => {
  it("links follow moving endpoints without mutating spatial input", () => {
    const before = interactionFrame([parent, child], [], positions, 0);
    const moved = new Map(positions); moved.set(child.id, { x: 900, y: 200, scale: 1 });
    moved.set(parent.id, { x: 300, y: 500, scale: 1 });
    expect(interactionFrame([parent, child], [], moved, 100).strokes[0]).toMatchObject({ from: { x: 300, y: 480 }, to: { x: 900, y: 180 } });
    expect(before.strokes[0].to).toEqual({ x: 800, y: 380 });
    expect(positions.get(child.id)).toEqual({ x: 800, y: 400, scale: 1 });
  });
  it("cleared wait/filtered or missing endpoints leave no ghosts", () => {
    expect(interactionFrame([{ ...parent, status: "thinking" }, child], [], positions, 0).strokes).toEqual([]);
    expect(interactionFrame([parent], [cue], positions, 1000).strokes).toEqual([]);
    expect(interactionFrame([parent, child], [cue], new Map(), 1000).strokes).toEqual([]);
  });
  it("transients travel in confirmed direction and disappear at expiry", () => {
    const at = (now: number) => interactionFrame([{ ...parent, status: "thinking" }, child], [cue], positions, now);
    expect(at(0).strokes[0]).toMatchObject({ from: { x: 800, y: 380 }, to: { x: 200, y: 280 }, progress: 0 });
    expect(at(1500).strokes[0].progress).toBe(0.5); expect(at(3000).strokes).toEqual([]);
  });
  it("user attention suppresses travelling packets and quiets coordination", () => {
    const waiting = { ...child, status: "waiting" as const, waiting_reason: "user_input" };
    expect(interactionFrame([parent, waiting], [cue], positions, 1000).strokes).toMatchObject([{ kind: "coordination", quiet: true }]);
  });
  it("error keeps non-color signal after transient emphasis, without parent error", () => {
    const error = { ...child, status: "error" as const };
    const blocked: InteractionCue = { ...cue, kind: "blocked", targetAgentId: undefined };
    expect(interactionFrame([parent, error], [blocked], positions, 1000).blocked).toMatchObject([{ id: child.id, emphasis: true }]);
    expect(interactionFrame([parent, error], [blocked], positions, 3000).blocked).toMatchObject([{ id: child.id, emphasis: false }]);
    expect(interactionDescription([parent, error], [], 0)).toContain("Tester: blocked");
    expect(interactionDescription([parent], [], 0)).not.toContain("waiting on");
  });
  it("reuses keyed primitives, removes missing endpoints and destroys resources", () => {
    const stage = new Container(), layer = new InteractionLayer(stage);
    layer.setState([parent, child], [cue]); layer.draw(positions, 1000);
    const badge = layer.connectors.children[1]; layer.draw(positions, 1200);
    expect(layer.connectors.children[1]).toBe(badge); expect(layer.connectors.zIndex).toBeLessThan(100);
    layer.setState([parent], [cue]); layer.draw(positions, 1300);
    expect(layer.connectors.children).toHaveLength(1); expect(badge.destroyed).toBe(true);
    layer.destroy(); expect(stage.children).toHaveLength(0);
  });
});

it("focus reuses badges, reduced motion keeps static symbols and respects original expiry", () => {
  const stage = new Container(), layer = new InteractionLayer(stage);
  const agents = [{ ...parent, status: "thinking" as const }, child];
  layer.setState(agents, [cue]);
  layer.setPresentation(child.id, focusFor(agents, child.id, null, [cue], 1000), true);
  layer.draw(positions, 1000);
  const badge = layer.markers.children[0];
  const before = { x: badge.x, y: badge.y };
  layer.draw(positions, 2000);
  expect(layer.markers.children[0]).toBe(badge);
  expect({ x: badge.x, y: badge.y }).toEqual(before);
  expect((badge as Container).children).toHaveLength(2);
  layer.setPresentation(null, new Map(), false); layer.draw(positions, 2500);
  expect(layer.markers.children[0]).toBe(badge);
  expect({ x: badge.x, y: badge.y }).not.toEqual(before);
  layer.draw(positions, 3000); expect(badge.destroyed).toBe(true);
  expect(cue.expiresAt).toBe(3000); layer.destroy();
});

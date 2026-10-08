import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OfficeScene } from "./OfficeScene";
import { demoAgents } from "../data/demo";

const sceneryMocks = vi.hoisted(() => ({
  setAtmosphere: vi.fn(),
  drawOfficeScenery: vi.fn(),
  scenes: [] as { stage: import("pixi.js").Container; tick: ((ticker: { deltaTime: number }) => void) | null }[],
}));

vi.mock("pixi.js", async () => {
  const canvasContext = vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(null);
  const actual = await vi.importActual<typeof import("pixi.js")>("pixi.js");
  canvasContext.mockRestore();
  return { ...actual,
  Application: class {
    canvas = document.createElement("canvas");
    renderer = {};
    stage = new actual.Container();
    observation = { stage: this.stage, tick: null as ((ticker: { deltaTime: number }) => void) | null };
    ticker = { add: (tick: (ticker: { deltaTime: number }) => void) => { this.observation.tick = tick; }, lastTime: 0 };

    constructor() { sceneryMocks.scenes.push(this.observation); }

    async init(options: { width: number; height: number }) {
      this.canvas.width = options.width;
      this.canvas.height = options.height;
      this.canvas.style.width = `${options.width}px`;
      this.canvas.style.height = `${options.height}px`;
    }

    destroy() {}
  },
  };
});

vi.mock("./scenery", () => ({
  drawOfficeScenery: sceneryMocks.drawOfficeScenery.mockReturnValue({
    setAtmosphere: sceneryMocks.setAtmosphere,
  }),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  sceneryMocks.scenes.length = 0;
});

const figures = (stage: import("pixi.js").Container) => stage.children.filter((child) => !child.label?.startsWith("interaction-"));

describe("OfficeScene", () => {
  it.each(["steady", "uneven"])("simultaneous arrivals reach their areas with %s frame timing", async (timing) => {
    const team = demoAgents.slice(0, 6).map((agent) => ["backend", "tester", "researcher"].includes(agent.id)
      ? { ...agent, status: "thinking" as const } : agent);
    render(<OfficeScene agents={team} deskCount={8} />);
    await waitFor(() => expect(figures(sceneryMocks.scenes[0].stage)).toHaveLength(6));
    const scene = sceneryMocks.scenes[0];
    for (let frame = 0; frame < 2000; frame++) scene.tick?.({ deltaTime: timing === "steady" ? 1 : [0.5, 1.5, 3][frame % 3] });
    const destinations = [[250, 244], [891, 371], [865, 170], [87, 132], [433, 561], [87, 462]];
    figures(scene.stage).forEach((figure, index) => {
      expect(Math.hypot(figure.x - destinations[index][0], figure.y - destinations[index][1]), team[index].id).toBeLessThan(4);
    });
  });

  it("updates semantic destinations incrementally and holds DONE at its current position", async () => {
    const tester = { ...demoAgents[1], status: "thinking" as const };
    const { rerender } = render(<OfficeScene agents={[tester]} deskCount={8} />);
    await waitFor(() => expect(figures(sceneryMocks.scenes[0].stage)).toHaveLength(1));
    const scene = sceneryMocks.scenes[0];
    const figure = figures(scene.stage)[0];
    for (let frame = 0; frame < 300; frame++) scene.tick?.({ deltaTime: 1 });
    // Existing routing considers a waypoint reached within four pixels.
    expect(Math.hypot(figure.x - 891, figure.y - 371)).toBeLessThan(4);
    const before = { x: figure.x, y: figure.y };
    rerender(<OfficeScene agents={[{ ...tester, status: "done" }]} deskCount={8} />);
    for (let frame = 0; frame < 100; frame++) scene.tick?.({ deltaTime: 1 });
    expect({ x: figure.x, y: figure.y }).toEqual(before);
    expect(figures(scene.stage)[0]).toBe(figure);
    expect(sceneryMocks.scenes).toHaveLength(1);
    expect(sceneryMocks.drawOfficeScenery).toHaveBeenCalledTimes(1);
  });

  it("interaction updates preserve settled positions and teardown releases overlay resources", async () => {
    const agents = [demoAgents[0], { ...demoAgents[1], status: "thinking" as const }];
    const view = render(<OfficeScene agents={agents} deskCount={8} />);
    await waitFor(() => expect(figures(sceneryMocks.scenes[0].stage)).toHaveLength(2));
    const scene = sceneryMocks.scenes[0];
    for (let i = 0; i < 900; i++) scene.tick?.({ deltaTime: 1 });
    const before = figures(scene.stage).map((a) => [a.x, a.y]);
    const now = Date.now();
    view.rerender(<OfficeScene agents={agents} deskCount={8} cues={[{
      id: "delegation", kind: "delegation", sourceAgentId: agents[0].id, targetAgentId: agents[1].id,
      createdAt: now, expiresAt: now + 3000,
    }]} />);
    scene.tick?.({ deltaTime: 1 });
    expect(figures(scene.stage).map((a) => [a.x, a.y])).toEqual(before);
    const markers = scene.stage.children.find((a) => a.label === "interaction-markers") as import("pixi.js").Container;
    expect(markers.children).toHaveLength(1);
    expect(sceneryMocks.scenes).toHaveLength(1);
    view.unmount();
    expect(markers.destroyed).toBe(true);
    expect(scene.stage.children.some((a) => a.label?.startsWith("interaction-"))).toBe(false);
  });

  it("exposes content-free user attention in the accessible scene description", async () => {
    const waiting = { ...demoAgents[1], status: "waiting" as const, waiting_reason: "user_input" };
    const view = render(<OfficeScene agents={[waiting]} deskCount={8} />);
    expect(view.getByRole("img")).toHaveAccessibleName(/Tester: waiting, \? Needs you/);
    await waitFor(() => expect(figures(sceneryMocks.scenes[0].stage)).toHaveLength(1));
  });
  it("fits the complete office canvas inside its responsive host", async () => {
    const { container } = render(<OfficeScene agents={[]} deskCount={8} />);

    await waitFor(() => {
      expect(container.querySelector("canvas")).toHaveClass("office-canvas");
    });

    const canvas = container.querySelector("canvas");
    expect(canvas).toHaveStyle({ width: "100%", height: "100%" });
    expect(canvas).toHaveAttribute("width", "1100");
    expect(canvas).toHaveAttribute("height", "680");
  });

  it("updates the city and indoor lighting when remaining usage changes", async () => {
    const { rerender } = render(<OfficeScene agents={[]} deskCount={8} usage={{
      status: "available",
      remaining_percent: 72,
      limiting_window: null,
      primary: null,
      secondary: null,
      individual: null,
      plan_type: null,
      updated_at: null,
    }} />);

    await waitFor(() => {
      expect(sceneryMocks.drawOfficeScenery).toHaveBeenCalledWith(expect.anything(), "day");
    });

    rerender(<OfficeScene agents={[]} deskCount={8} usage={{
      status: "available",
      remaining_percent: 18,
      limiting_window: null,
      primary: null,
      secondary: null,
      individual: null,
      plan_type: null,
      updated_at: null,
    }} />);

    await waitFor(() => {
      expect(sceneryMocks.setAtmosphere).toHaveBeenCalledWith("night");
    });
  });
});

import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OfficeScene } from "./OfficeScene";

const sceneryMocks = vi.hoisted(() => ({
  setAtmosphere: vi.fn(),
  drawOfficeScenery: vi.fn(),
}));

vi.mock("pixi.js", () => ({
  Application: class {
    canvas = document.createElement("canvas");
    renderer = {};
    stage = { sortableChildren: false };
    ticker = { add: vi.fn(), lastTime: 0 };

    async init(options: { width: number; height: number }) {
      this.canvas.width = options.width;
      this.canvas.height = options.height;
      this.canvas.style.width = `${options.width}px`;
      this.canvas.style.height = `${options.height}px`;
    }

    destroy() {}
  },
  Container: class {},
  Graphics: class {},
  Text: class {},
}));

vi.mock("./scenery", () => ({
  drawOfficeScenery: sceneryMocks.drawOfficeScenery.mockReturnValue({
    setAtmosphere: sceneryMocks.setAtmosphere,
  }),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("OfficeScene", () => {
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

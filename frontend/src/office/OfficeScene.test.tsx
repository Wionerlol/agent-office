import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OfficeScene } from "./OfficeScene";

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

vi.mock("./scenery", () => ({ drawOfficeScenery: vi.fn() }));

afterEach(cleanup);

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
});

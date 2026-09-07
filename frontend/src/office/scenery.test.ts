import type { Application, Bounds, Container, Graphics } from "pixi.js";
import { describe, expect, it, vi } from "vitest";

import { POSITIONS } from "./layout";

function renderedDeskBounds(
  background: Container,
  GraphicsClass: typeof Graphics,
  deskId: string,
): Bounds {
  const point = POSITIONS[deskId];
  const candidates = background.children
    .filter((child): child is Graphics => child instanceof GraphicsClass)
    .map((child) => child.getBounds())
    .filter((bounds) => (
      bounds.minX <= point.x
      && bounds.maxX >= point.x
      && bounds.minY <= point.y
      && bounds.maxY >= point.y
    ))
    .sort((left, right) => left.width * left.height - right.width * right.height);
  return candidates[0];
}

describe("office scenery geometry", () => {
  it("keeps the panoramic window and both desk rows visually separate", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const [{ Container, Graphics }, { drawOfficeScenery }] = await Promise.all([
      import("pixi.js"),
      import("./scenery"),
    ]);
    consoleError.mockRestore();
    const stage = new Container();
    drawOfficeScenery({ stage } as Application, "day");
    const background = stage.children[0] as Container;
    const cityWindow = stage.children[1] as Container;
    const windowGraphics = cityWindow.children.find((child) => child instanceof Graphics);
    const windowBounds = windowGraphics!.getBounds();

    for (let column = 1; column <= 4; column += 1) {
      const firstRow = renderedDeskBounds(background, Graphics, `desk-${column}`);
      const secondRow = renderedDeskBounds(background, Graphics, `desk-${column + 4}`);
      expect(firstRow.minY - windowBounds.maxY, `desk-${column}`).toBeGreaterThanOrEqual(8);
      expect(secondRow.minY - firstRow.maxY, `desk rows ${column}`).toBeGreaterThanOrEqual(8);
    }
  });
});

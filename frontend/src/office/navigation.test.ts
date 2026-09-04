import { describe, expect, it } from "vitest";

import { POSITIONS, spreadAgentTargets } from "./layout";
import { findPath, isOfficePositionWalkable, routeBetween } from "./navigation";

describe("findPath", () => {
  it("routes around blocked office cells", () => {
    const path = findPath(
      { x: 0, y: 1 },
      { x: 4, y: 1 },
      new Set(["1,1", "2,1", "3,1"]),
      5,
      3,
    );

    expect(path[0]).toEqual({ x: 0, y: 1 });
    expect(path.at(-1)).toEqual({ x: 4, y: 1 });
    expect(path).not.toContainEqual({ x: 2, y: 1 });
    expect(path.length).toBe(7);
  });
});

describe("office routing", () => {
  it("enters the library through its doorway instead of crossing the wall", () => {
    const start = { x: 700, y: 160 };
    const path = [start, ...routeBetween(start, { x: 942, y: 169 })];
    const dividerX = 796;
    const crossingY = path.slice(1).flatMap((point, index) => {
      const previous = path[index];
      if ((previous.x - dividerX) * (point.x - dividerX) > 0) return [];
      const progress = (dividerX - previous.x) / (point.x - previous.x);
      return previous.y + (point.y - previous.y) * progress;
    });

    expect(crossingY.some((y) => y >= 165 && y <= 215)).toBe(true);
  });

  it("can reach shared-area slots without using a direct obstacle fallback", () => {
    for (const zone of ["library", "coffee_area", "lounge", "tool_lab", "test_lab", "exit"]) {
      const slots = spreadAgentTargets(
        Array.from({ length: 8 }, (_, index) => ({ id: `agent-${index}`, zone })),
      );
      for (const destination of slots.values()) {
        expect(isOfficePositionWalkable(destination), `${zone}: ${destination.x},${destination.y}`).toBe(true);
        expect(routeBetween(POSITIONS["desk-1"], destination).length).toBeGreaterThan(0);
      }
    }
  });
});

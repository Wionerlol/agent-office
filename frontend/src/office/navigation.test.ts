import { describe, expect, it } from "vitest";

import { findPath } from "./navigation";

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

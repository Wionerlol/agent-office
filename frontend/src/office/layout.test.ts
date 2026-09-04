import { describe, expect, it } from "vitest";

import { assignDesk, separateAgentPositions, spreadAgentTargets } from "./layout";

describe("assignDesk", () => {
  it("uses each available desk before sharing one", () => {
    const assignments = new Map<string, string>();
    const assigned = ["one", "two", "three", "four", "five", "six", "seven", "eight"].map((id) =>
      assignDesk(id, assignments),
    );

    expect(new Set(assigned).size).toBe(8);
    expect(assignDesk("one", assignments)).toBe(assigned[0]);

    expect(assignDesk("eight", assignments, 2)).toMatch(/^desk-[12]$/);
  });
});

describe("spreadAgentTargets", () => {
  it("gives agents in one area stable, non-overlapping destinations", () => {
    const targets = [
      { id: "alpha", zone: "library" },
      { id: "bravo", zone: "library" },
      { id: "charlie", zone: "library" },
    ];

    const positions = spreadAgentTargets(targets);
    const reversed = spreadAgentTargets([...targets].reverse());

    expect(new Set([...positions.values()].map(({ x, y }) => `${x},${y}`)).size).toBe(3);
    for (const target of targets) {
      expect(reversed.get(target.id)).toEqual(positions.get(target.id));
    }
    const values = [...positions.values()];
    for (let left = 0; left < values.length; left += 1) {
      for (let right = left + 1; right < values.length; right += 1) {
        const deltaX = Math.abs(values[left].x - values[right].x);
        const deltaY = Math.abs(values[left].y - values[right].y);
        expect(deltaX >= 100 || deltaY >= 110).toBe(true);
      }
    }
  });

  it("separates agents that meet while walking", () => {
    const positions = separateAgentPositions([
      { id: "alpha", x: 500, y: 300 },
      { id: "bravo", x: 500, y: 300 },
      { id: "charlie", x: 500, y: 300 },
    ]);
    const values = [...positions.values()];

    for (let left = 0; left < values.length; left += 1) {
      for (let right = left + 1; right < values.length; right += 1) {
        expect(Math.hypot(
          values[left].x - values[right].x,
          values[left].y - values[right].y,
        )).toBeGreaterThanOrEqual(49.9);
      }
    }
  });
});

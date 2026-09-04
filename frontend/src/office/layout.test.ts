import { describe, expect, it } from "vitest";

import { assignDesk, separateAgentPositions, spreadAgentTargets, ZONES } from "./layout";

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
        const first = values[left];
        const second = values[right];
        const firstWidth = (first.showLabel ? 96 : 46) * first.scale;
        const secondWidth = (second.showLabel ? 96 : 46) * second.scale;
        const firstHeight = (first.showLabel ? 108 : 69) * first.scale;
        const secondHeight = (second.showLabel ? 108 : 69) * second.scale;
        const deltaX = Math.abs(first.x - second.x);
        const deltaY = Math.abs(first.y - second.y);
        expect(
          deltaX >= (firstWidth + secondWidth) / 2
          || deltaY >= (firstHeight + secondHeight) / 2,
        ).toBe(true);
      }
    }
  });

  it("keeps crowded shared zones inside their rooms by scaling the figures", () => {
    for (const zone of ["entrance", "library", "coffee_area", "lounge", "tool_lab", "test_lab", "exit"]) {
      const room = ZONES.find(({ id }) => id === zone)!;
      const positions = spreadAgentTargets(
        Array.from({ length: 8 }, (_, index) => ({ id: `agent-${index}`, zone })),
      );

      for (const position of positions.values()) {
        expect(position.x - 23 * position.scale).toBeGreaterThanOrEqual(room.x);
        expect(position.x + 23 * position.scale).toBeLessThanOrEqual(room.x + room.width);
        expect(position.y - 46 * position.scale).toBeGreaterThanOrEqual(room.y);
        expect(position.y + 23 * position.scale).toBeLessThanOrEqual(room.y + room.height);
      }
    }
  });

  it("separates agents that meet while walking", () => {
    const positions = separateAgentPositions(
      Array.from({ length: 8 }, (_, index) => ({
        id: `agent-${index}`,
        x: 85,
        y: 370,
      })),
    );
    const values = [...positions.values()];

    for (const position of values) {
      expect(position.x).toBeGreaterThanOrEqual(49);
      expect(position.x).toBeLessThanOrEqual(1051);
      expect(position.y).toBeGreaterThanOrEqual(73);
      expect(position.y).toBeLessThanOrEqual(625);
    }

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

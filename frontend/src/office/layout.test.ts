import { describe, expect, it } from "vitest";

import { assignDesk } from "./layout";

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

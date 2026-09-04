import { describe, expect, it } from "vitest";

import { assignDesk } from "./layout";

describe("assignDesk", () => {
  it("uses each available desk before sharing one", () => {
    const assignments = new Map<string, string>();
    const assigned = ["one", "two", "three", "four", "five"].map((id) =>
      assignDesk(id, assignments),
    );

    expect(new Set(assigned).size).toBe(5);
    expect(assignDesk("one", assignments)).toBe(assigned[0]);
  });
});

import { describe, expect, it } from "vitest";

import { atmosphereForUsage } from "./atmosphere";

describe("Codex usage atmosphere", () => {
  it.each([
    [100, "day"],
    [50, "day"],
    [49.9, "dusk"],
    [20, "dusk"],
    [19.9, "night"],
    [0, "night"],
    [null, "day"],
  ] as const)("maps %s percent remaining to %s", (remaining, expected) => {
    expect(atmosphereForUsage(remaining)).toBe(expected);
  });
});

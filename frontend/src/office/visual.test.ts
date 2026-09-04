import { describe, expect, it } from "vitest";

import { visualFor } from "./visual";

describe("visualFor", () => {
  it("projects backend state into office behavior", () => {
    expect(visualFor("coding", "desk-3")).toEqual({
      zone: "desk-3",
      animation: "typing",
    });
    expect(visualFor("testing", "desk-3")).toEqual({
      zone: "test_lab",
      animation: "testing",
    });
    expect(visualFor("offline", "desk-3")).toEqual({
      zone: "exit",
      animation: "leaving",
    });
  });
});

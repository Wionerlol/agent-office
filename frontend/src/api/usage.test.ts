import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useAgentStore } from "../store/agents";
import { observeCodexUsage } from "./usage";

describe("Codex usage monitoring", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useAgentStore.getState().reset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it("loads immediately and refreshes the remaining allowance", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        status: "available",
        remaining_percent: 64,
        limiting_window: "primary",
        primary: null,
        secondary: null,
        individual: null,
        plan_type: "plus",
        updated_at: "2026-09-05T01:00:00Z",
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        status: "available",
        remaining_percent: 18,
        limiting_window: "primary",
        primary: null,
        secondary: null,
        individual: null,
        plan_type: "plus",
        updated_at: "2026-09-05T01:01:00Z",
      }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const stop = observeCodexUsage(30_000);
    await vi.waitFor(() => {
      expect(useAgentStore.getState().codexUsage?.remaining_percent).toBe(64);
    });

    await vi.advanceTimersByTimeAsync(30_000);
    await vi.waitFor(() => {
      expect(useAgentStore.getState().codexUsage?.remaining_percent).toBe(18);
    });

    stop();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});

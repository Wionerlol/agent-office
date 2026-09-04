import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { CodexUsage } from "../models/agent";
import { CodexUsageIndicator } from "./CodexUsageIndicator";

describe("CodexUsageIndicator", () => {
  it("explains the usage level represented by the office lighting", () => {
    const usage: CodexUsage = {
      status: "available",
      remaining_percent: 18,
      limiting_window: "primary",
      primary: {
        used_percent: 82,
        remaining_percent: 18,
        window_minutes: 300,
        resets_at: "2026-09-05T04:00:00Z",
      },
      secondary: null,
      individual: null,
      plan_type: "plus",
      updated_at: "2026-09-05T01:00:00Z",
    };

    render(<CodexUsageIndicator usage={usage} />);

    expect(screen.getByText("18% remaining")).toBeInTheDocument();
    expect(screen.getByText("Deep night")).toBeInTheDocument();
    expect(screen.getByText(/5h window/)).toBeInTheDocument();
  });
});

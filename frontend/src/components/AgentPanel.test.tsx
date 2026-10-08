import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Agent } from "../models/agent";
import { AgentPanel } from "./AgentPanel";

const legacy: Agent = {
  id: "worker", name: "Codex 42", provider: "codex", pid: 42, repository: "/repo",
  worktree: null, branch: null, status: "thinking", task: "Verify auth", current_tool: null,
  changed_files: [], started_at: "2026-10-02T00:00:00Z", last_active_at: "2026-10-02T00:00:00Z",
  metadata: {},
};

afterEach(cleanup);

describe("AgentPanel semantic identity", () => {
  it("shows stable identity, responsibilities, parent, and separate runtime facts", () => {
    const agent: Agent = { ...legacy, name: "Tester", role: "tester",
      responsibilities: ["Run unit tests", "Investigate failures"], parent_agent_id: "lead",
      definition_id: "tester", status: "testing", current_tool: "pytest" };
    render(<AgentPanel agent={agent} events={[]} onClose={() => undefined} />);
    expect(screen.getByRole("heading", { name: "Tester" })).toBeInTheDocument();
    expect(screen.getByText("Role").nextElementSibling).toHaveTextContent("tester");
    expect(screen.getByText("Responsibilities").nextElementSibling).toHaveTextContent("Run unit tests");
    expect(screen.getByText("Investigate failures")).toBeInTheDocument();
    expect(screen.getByText("Parent Agent").nextElementSibling).toHaveTextContent("Not in this view");
    expect(screen.getByText("Current Task").nextElementSibling).toHaveTextContent("Verify auth");
    expect(screen.getByText("Current State").nextElementSibling).toHaveTextContent("testing");
    expect(screen.getByText("Current Tool").nextElementSibling).toHaveTextContent("pytest");
  });

  it("renders older agents with optional semantic fields absent", () => {
    render(<AgentPanel agent={legacy} events={[]} onClose={() => undefined} />);
    expect(screen.getByRole("heading", { name: "Codex 42" })).toBeInTheDocument();
    expect(screen.getByText("Role").nextElementSibling).toHaveTextContent("—");
    expect(screen.queryByText("Responsibilities")).not.toBeInTheDocument();
    expect(screen.queryByText("Parent Agent")).not.toBeInTheDocument();
    expect(screen.queryByText("Definition")).not.toBeInTheDocument();
  });

  it("preserves a Backend identity while activity and executable change", () => {
    const agent: Agent = { ...legacy, name: "Backend Engineer", role: "backend" };
    const { rerender } = render(<AgentPanel agent={agent} events={[]} onClose={() => undefined} />);
    rerender(<AgentPanel agent={{ ...agent, status: "testing", current_tool: "pytest" }} events={[]} onClose={() => undefined} />);
    expect(screen.getByRole("heading", { name: "Backend Engineer" })).toBeInTheDocument();
    expect(screen.getByText("Role").nextElementSibling).toHaveTextContent("backend");
    expect(screen.getByText("Current State").nextElementSibling).toHaveTextContent("testing");
  });
});

describe("AgentPanel waiting context", () => {
  it("distinguishes user input from idle and hides cleared context", () => {
    const agent: Agent = { ...legacy, status: "waiting", waiting_reason: "user_input" };
    const { rerender } = render(<AgentPanel agent={agent} events={[]} onClose={() => undefined} />);
    expect(screen.getByText("Waiting for user input")).toBeInTheDocument();
    rerender(<AgentPanel agent={{ ...agent, status: "idle", waiting_reason: null }}
      events={[]} onClose={() => undefined} />);
    expect(screen.queryByText("Waiting reason")).not.toBeInTheDocument();
    expect(screen.getByText("Current State").nextElementSibling).toHaveTextContent("idle");
  });

  it("renders a deterministic child wait through normalized fields", () => {
    render(<AgentPanel agent={{ ...legacy, status: "waiting", waiting_reason: "child_agent",
      waiting_on_agent_id: "tester-child" }} events={[]} onClose={() => undefined} />);
    expect(screen.getByText("Waiting for child agent")).toBeInTheDocument();
    expect(screen.getByText("Waiting on Agent").nextElementSibling).toHaveTextContent("Not in this view");
  });
});

 it("navigates only visible direct parent, children and waiting target", () => {
  const lead = { ...legacy, id: "lead", name: "Lead", parent_agent_id: "grandparent", status: "waiting" as const, waiting_reason: "child_agent", waiting_on_agent_id: "tester" };
  const tester = { ...legacy, id: "tester", name: "Tester", parent_agent_id: "lead" };
  const grandparent = { ...legacy, id: "grandparent", name: "Owner" };
  const grandchild = { ...legacy, id: "grandchild", name: "Not direct", parent_agent_id: "tester" };
  const select = vi.fn();
  render(<AgentPanel agent={lead} visibleAgents={[lead, tester, grandparent, grandchild]} events={[]} onClose={() => undefined} onSelect={select} />);
  fireEvent.click(screen.getByRole("button", { name: "Owner" }));
  for (const button of screen.getAllByRole("button", { name: "Tester" })) fireEvent.click(button);
  expect(select.mock.calls).toEqual([["grandparent"], ["tester"], ["tester"]]);
  expect(screen.queryByText("Not direct")).not.toBeInTheDocument();
});

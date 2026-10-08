import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { demoAgents } from "../data/demo";
import { AgentNavigator } from "./AgentNavigator";

afterEach(cleanup);
it("offers native keyboard buttons, pressed announcement and visible attention/status", () => {
  const select = vi.fn(), clear = vi.fn();
  const view = render(<AgentNavigator agents={demoAgents} selectedId="tester" onSelect={select} onClear={clear} />);
  const button = screen.getByRole("button", { name: "Tester, testing" });
  expect(button).toHaveAttribute("aria-pressed", "true"); button.focus(); expect(button).toHaveFocus();
  fireEvent.click(button); expect(select).toHaveBeenCalledWith("tester");
  expect(screen.getByRole("status")).toHaveTextContent("Tester selected");
  expect(screen.getByRole("button", { name: /Frontend Engineer.*needs you/ })).toBeInTheDocument();
  fireEvent.keyDown(window, { key: "Escape" }); expect(clear).toHaveBeenCalledTimes(1);
  view.unmount(); fireEvent.keyDown(window, { key: "Escape" }); expect(clear).toHaveBeenCalledTimes(1);
});

import { act, renderHook } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { useReducedMotion } from "./useReducedMotion";

it("shares the system preference with live updates and removes its subscription", () => {
  let notify: (() => void) | undefined;
  const media = { matches: false, addEventListener: vi.fn((_type, fn) => { notify = fn; }), removeEventListener: vi.fn() };
  vi.stubGlobal("matchMedia", vi.fn(() => media));
  const { result, unmount } = renderHook(useReducedMotion);
  expect(result.current).toBe(false);
  act(() => { media.matches = true; notify?.(); }); expect(result.current).toBe(true);
  expect(media.addEventListener).toHaveBeenCalledTimes(1);
  unmount(); expect(media.removeEventListener).toHaveBeenCalledWith("change", notify);
  vi.unstubAllGlobals();
});

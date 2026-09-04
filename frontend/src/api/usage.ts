import type { CodexUsage } from "../models/agent";
import { useAgentStore } from "../store/agents";

function isCodexUsage(value: unknown): value is CodexUsage {
  if (!value || typeof value !== "object") return false;
  const candidate = value as { status?: unknown; remaining_percent?: unknown };
  return (
    (candidate.status === "available" || candidate.status === "unavailable")
    && (candidate.remaining_percent === null || typeof candidate.remaining_percent === "number")
  );
}

async function refreshCodexUsage(): Promise<void> {
  const response = await fetch("/api/codex-usage");
  if (!response.ok) throw new Error(`Codex usage request failed: ${response.status}`);
  const usage: unknown = await response.json();
  if (!isCodexUsage(usage)) throw new Error("Codex usage response was invalid");
  useAgentStore.getState().setCodexUsage(usage);
}

export function observeCodexUsage(intervalMs = 30_000): () => void {
  let stopped = false;
  let timer: number | undefined;

  const refresh = async () => {
    try {
      await refreshCodexUsage();
    } catch (error) {
      console.warn("Unable to refresh Codex usage", error);
    } finally {
      if (!stopped) timer = window.setTimeout(refresh, intervalMs);
    }
  };

  void refresh();
  return () => {
    stopped = true;
    if (timer) window.clearTimeout(timer);
  };
}

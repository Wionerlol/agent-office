import type { CodexUsage, CodexUsageWindow } from "../models/agent";
import { atmosphereForUsage, type OfficeAtmosphere } from "../office/atmosphere";

const atmosphereLabels: Record<OfficeAtmosphere, string> = {
  day: "Daylight",
  dusk: "Sunset",
  night: "Deep night",
};

const atmosphereIcons: Record<OfficeAtmosphere, string> = {
  day: "☀",
  dusk: "◐",
  night: "☾",
};

function windowForUsage(usage: CodexUsage): CodexUsageWindow | null {
  if (usage.limiting_window === "primary") return usage.primary;
  if (usage.limiting_window === "secondary") return usage.secondary;
  if (usage.limiting_window === "individual") return usage.individual;
  return null;
}

function windowLabel(minutes: number): string {
  if (minutes % 10_080 === 0) return `${minutes / 10_080}w window`;
  if (minutes % 1_440 === 0) return `${minutes / 1_440}d window`;
  if (minutes % 60 === 0) return `${minutes / 60}h window`;
  return `${minutes}m window`;
}

function resetLabel(resetsAt: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(resetsAt));
}

export function CodexUsageIndicator({ usage }: { usage: CodexUsage | null }) {
  const remaining = usage?.status === "available" ? usage.remaining_percent : null;
  const atmosphere = atmosphereForUsage(remaining);
  const limitingWindow = usage ? windowForUsage(usage) : null;

  return (
    <div className={`usage-indicator usage-${atmosphere}`} title="Office daylight follows Codex usage remaining">
      <span className="usage-icon" aria-hidden="true">{atmosphereIcons[atmosphere]}</span>
      <span className="usage-copy">
        <small>Codex capacity</small>
        {remaining === null ? (
          <strong>Waiting for usage data</strong>
        ) : (
          <strong>{Math.round(remaining)}% remaining</strong>
        )}
      </span>
      <span className="usage-detail">
        <strong>{atmosphereLabels[atmosphere]}</strong>
        {limitingWindow && (
          <small>{windowLabel(limitingWindow.window_minutes)} · resets {resetLabel(limitingWindow.resets_at)}</small>
        )}
      </span>
    </div>
  );
}

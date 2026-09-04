import type { Agent } from "../models/agent";

export function Achievements({ agents }: { agents: Agent[] }) {
  const achievements = [
    agents.length >= 2 && "Crew assembled",
    agents.some((agent) => agent.status === "testing") && "Test lab active",
    agents.some((agent) => agent.status === "done") && "Milestone shipped",
    agents.some((agent) => agent.status === "error") && "Needs attention",
  ].filter(Boolean) as string[];
  if (!achievements.length) return null;
  return <div className="achievements" aria-label="Office achievements">{achievements.map((item) => <span key={item}>◆ {item}</span>)}</div>;
}

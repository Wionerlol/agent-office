import { Container, Graphics, Text } from "pixi.js";
import type { Agent } from "../models/agent";
import { coordinationLinks, type InteractionCue } from "../models/interaction";
import { connectorEmphasis, type AgentFocus } from "./focus";
import type { Point } from "./layout";

export interface AgentPosition extends Point { scale: number }
export interface InteractionStroke {
  id: string;
  kind: "coordination" | "delegation" | "handoff";
  sourceAgentId: string;
  targetAgentId: string;
  from: Point;
  to: Point;
  progress: number;
  quiet: boolean;
}
export interface InteractionFrame {
  strokes: InteractionStroke[];
  blocked: { id: string; point: Point; emphasis: boolean }[];
}

const needsUser = (a: Agent) => a.status === "waiting" && a.waiting_reason === "user_input";
const endpoint = (p: AgentPosition): Point => ({ x: p.x, y: p.y - 20 * p.scale });

/** Resolve endpoints from the rendered subset every frame; never owns movement or truth. */
export function interactionFrame(agents: readonly Agent[], cues: readonly InteractionCue[], positions: ReadonlyMap<string, AgentPosition>, now: number): InteractionFrame {
  const visible = new Map(agents.filter((a) => a.status !== "offline" && positions.has(a.id)).map((a) => [a.id, a]));
  const pair = (source: string, target: string) => visible.has(source) && visible.has(target)
    ? { from: endpoint(positions.get(source)!), to: endpoint(positions.get(target)!) } : null;
  const strokes: InteractionStroke[] = [];
  for (const link of coordinationLinks([...visible.values()])) {
    const points = pair(link.sourceAgentId, link.targetAgentId);
    if (points) strokes.push({ id: `wait:${link.sourceAgentId}`, kind: "coordination", sourceAgentId: link.sourceAgentId, targetAgentId: link.targetAgentId, ...points, progress: 0.5,
      quiet: needsUser(visible.get(link.targetAgentId)!) });
  }
  const active = cues.filter((c) => c.createdAt <= now && c.expiresAt > now);
  for (const cue of active) {
    if (cue.kind === "blocked" || !cue.targetAgentId) continue;
    const points = pair(cue.sourceAgentId, cue.targetAgentId);
    // Explicit user attention stays strongest; do not fly another badge across its marker.
    if (points && !needsUser(visible.get(cue.sourceAgentId)!) && !needsUser(visible.get(cue.targetAgentId)!)) {
      strokes.push({ id: cue.id, kind: cue.kind, sourceAgentId: cue.sourceAgentId, targetAgentId: cue.targetAgentId, ...points,
        progress: (now - cue.createdAt) / (cue.expiresAt - cue.createdAt), quiet: false });
    }
  }
  return { strokes, blocked: [...visible.values()].filter((a) => a.status === "error").map((a) => ({
    id: a.id, point: endpoint(positions.get(a.id)!),
    emphasis: active.some((c) => c.kind === "blocked" && c.sourceAgentId === a.id),
  })) };
}

export function arcPoint(from: Point, to: Point, t: number): Point {
  const bend = Math.min(55, Math.hypot(to.x - from.x, to.y - from.y) * 0.14);
  return { x: from.x + (to.x - from.x) * t,
    y: from.y + (to.y - from.y) * t - 4 * t * (1 - t) * bend };
}

export function interactionDescription(agents: readonly Agent[], cues: readonly InteractionCue[], now: number): string {
  const byId = new Map(agents.filter((a) => a.status !== "offline").map((a) => [a.id, a]));
  const relations = coordinationLinks(agents).map((link) => `${byId.get(link.sourceAgentId)?.name} waiting on ${byId.get(link.targetAgentId)?.name}`);
  const transitions = cues.filter((c) => c.expiresAt > now && byId.has(c.sourceAgentId) && (!c.targetAgentId || byId.has(c.targetAgentId)))
    .map((c) => `${byId.get(c.sourceAgentId)!.name}: ${c.kind}${c.targetAgentId ? ` to ${byId.get(c.targetAgentId)!.name}` : ""}`);
  return [...relations, ...agents.filter((a) => a.status === "error").map((a) => `${a.name}: blocked`), ...transitions].join(". ");
}

/** Reuses one connector Graphics and keyed badges; owns no state, routes or timers. */
export class InteractionLayer {
  readonly connectors = new Container();
  readonly markers = new Container();
  private lines = new Graphics();
  private badges = new Map<string, Container>();
  private agents: readonly Agent[] = [];
  private cues: readonly InteractionCue[] = [];
  private selectedId: string | null = null;
  private focus: ReadonlyMap<string, AgentFocus> = new Map();
  private reducedMotion = false;

  constructor(stage: Container) {
    this.connectors.label = "interaction-connectors";
    this.markers.label = "interaction-markers";
    this.connectors.zIndex = 90;
    this.markers.zIndex = 950;
    this.connectors.eventMode = this.markers.eventMode = "none";
    this.connectors.addChild(this.lines);
    stage.addChild(this.connectors, this.markers);
  }

  setState(agents: readonly Agent[], cues: readonly InteractionCue[]): void { this.agents = agents; this.cues = cues; }

  setPresentation(selectedId: string | null, focus: ReadonlyMap<string, AgentFocus>, reducedMotion: boolean): void {
    this.selectedId = selectedId; this.focus = focus; this.reducedMotion = reducedMotion;
  }

  draw(positions: ReadonlyMap<string, AgentPosition>, now: number): void {
    const frame = interactionFrame(this.agents, this.cues, positions, now), used = new Set<string>();
    this.lines.clear();
    for (const stroke of frame.strokes) {
      const color = stroke.kind === "handoff" ? 0x46745b : stroke.kind === "delegation" ? 0x4c6585 : 0x607d78;
      const emphasis = connectorEmphasis(stroke.sourceAgentId, stroke.targetAgentId, this.selectedId, this.focus);
      const alpha = stroke.quiet ? 0.2 : emphasis === "quiet" ? 0.18 : emphasis === "focused" ? 0.9 : stroke.kind === "coordination" ? 0.5 : 0.65;
      for (let i = 0; i < 24; i += 2) {
        const a = arcPoint(stroke.from, stroke.to, i / 24), b = arcPoint(stroke.from, stroke.to, (i + 1) / 24);
        this.lines.moveTo(a.x, a.y).lineTo(b.x, b.y).stroke({ width: emphasis === "focused" ? 2.5 : 1.5, color, alpha });
      }
      const progress = this.reducedMotion ? 0.5 : stroke.progress;
      const point = arcPoint(stroke.from, stroke.to, progress);
      // Persistent relation has a small bidirectional glyph; travelling badges encode lifecycle direction.
      const next = arcPoint(stroke.from, stroke.to, progress + 0.01);
      const rotation = stroke.kind === "delegation" ? Math.atan2(next.y - point.y, next.x - point.x) : 0;
      this.badge(stroke.id, stroke.kind === "coordination" ? "↔" : stroke.kind === "handoff" ? "✓" : "→", point, color, stroke.quiet || emphasis === "quiet" ? 0.45 : 1, used, rotation);
    }
    for (const blocked of frame.blocked) {
      this.badge(`blocked:${blocked.id}`, "!", { x: blocked.point.x + 28, y: blocked.point.y - 38 }, 0x854a3d, 1, used);
      if (blocked.emphasis) this.lines.circle(blocked.point.x, blocked.point.y, 30).stroke({ width: 2, color: 0x854a3d, alpha: 0.65 });
    }
    for (const [id, badge] of this.badges) if (!used.has(id)) {
      badge.destroy({ children: true });
      this.badges.delete(id);
    }
  }

  private badge(id: string, text: string, point: Point, color: number, alpha: number, used: Set<string>, rotation = 0): void {
    used.add(id);
    let badge = this.badges.get(id);
    if (!badge) {
      const container = new Container(), plate = new Graphics();
      const label = new Text({ text, style: { fontFamily: "system-ui", fontSize: 10, fontWeight: "600", fill: color } });
      label.anchor.set(0.5);
      const width = text.length > 2 ? 76 : 20;
      plate.roundRect(-width / 2, -9, width, 18, 6).fill({ color: 0xf8f2e6, alpha: 0.96 }).stroke({ width: 1, color, alpha: 0.5 });
      container.label = id;
      container.addChild(plate, label);
      // The small persistent glyph stays under labels; short travelling pulses may cross foreground scenery.
      (id.startsWith("wait:") ? this.connectors : this.markers).addChild(container);
      badge = container;
      this.badges.set(id, badge);
    }
    badge.position.set(point.x, point.y);
    badge.alpha = alpha;
    badge.rotation = rotation;
  }

  destroy(): void {
    this.badges.clear();
    this.agents = []; this.cues = []; this.focus = new Map();
    this.connectors.destroy({ children: true });
    this.markers.destroy({ children: true });
  }
}

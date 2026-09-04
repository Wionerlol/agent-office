import { Application, Container, Graphics, Text } from "pixi.js";
import { useEffect, useRef, useState } from "react";

import type { Agent, CodexUsage } from "../models/agent";
import { useAgentStore } from "../store/agents";
import { atmosphereForUsage } from "./atmosphere";
import { assignDesk, OFFICE_HEIGHT, OFFICE_WIDTH, POSITIONS, separateAgentPositions, spreadAgentTargets, type Point } from "./layout";
import { isOfficePositionWalkable, routeBetween } from "./navigation";
import { drawOfficeScenery, type OfficeScenery } from "./scenery";
import { visualFor, type VisualState } from "./visual";

interface OfficeSceneProps {
  agents: Agent[];
  deskCount: number;
  usage?: CodexUsage | null;
}

interface RenderedAgent {
  container: Container;
  body: Container;
  labels: Container;
  name: Text;
  status: Text;
  path: Point[];
  targetZone: string;
  targetPoint: Point;
  showLabel: boolean;
  animation: VisualState;
  phase: number;
}

const agentColor = (id: string): number => {
  const palette = [0x3a7d78, 0xc46a4a, 0x6e6599, 0x4f789e, 0xa67c3d, 0x987070];
  return palette[[...id].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % palette.length];
};

const shortName = (name: string): string => name.length > 15 ? `${name.slice(0, 13)}…` : name;

function createRenderedAgent(agent: Agent, selectAgent: (id: string) => void): RenderedAgent {
  const container = new Container();
  container.eventMode = "static";
  container.cursor = "pointer";
  container.on("pointertap", () => selectAgent(agent.id));
  const color = agentColor(agent.id);
  const shadow = new Graphics().ellipse(0, 19, 22, 8).fill({ color: 0x263236, alpha: 0.22 });
  const body = new Container();
  const legs = new Graphics()
    .roundRect(-12, 5, 9, 17, 4)
    .roundRect(3, 5, 9, 17, 4)
    .fill(0x334447)
    .roundRect(-15, 17, 12, 6, 3)
    .roundRect(3, 17, 12, 6, 3)
    .fill(0x263234);
  const torso = new Graphics()
    .roundRect(-18, -19, 36, 31, 10)
    .fill(color)
    .roundRect(-23, -14, 7, 25, 4)
    .roundRect(16, -14, 7, 25, 4)
    .fill(color)
    .roundRect(-5, -15, 10, 13, 2)
    .fill({ color: 0xf5e7c9, alpha: 0.9 });
  const head = new Graphics()
    .circle(0, -31, 15)
    .fill(0xf0c9a5)
    .arc(0, -34, 15, Math.PI, Math.PI * 2)
    .fill(0x42352f)
    .circle(-5, -30, 1.6)
    .circle(5, -30, 1.6)
    .fill(0x253234)
    .moveTo(-4, -24)
    .quadraticCurveTo(0, -21, 4, -24)
    .stroke({ width: 1.5, color: 0x9b604f });
  body.addChild(legs, torso, head);

  const namePlate = new Graphics()
    .roundRect(-48, 29, 96, 19, 7)
    .fill({ color: 0xf8f2e6, alpha: 0.95 })
    .stroke({ width: 1, color: 0x314649, alpha: 0.3 });
  const name = new Text({ text: shortName(agent.name), style: { fontFamily: "system-ui", fontSize: 11, fill: 0x17262b, fontWeight: "600" } });
  name.anchor.set(0.5);
  name.position.set(0, 38);
  const status = new Text({ text: agent.status.toUpperCase(), style: { fontFamily: "monospace", fontSize: 8, fill: 0xe8f2ed, fontWeight: "600" } });
  status.anchor.set(0.5);
  status.position.set(0, 54);
  const statusPlate = new Graphics().roundRect(-33, 48, 66, 14, 7).fill({ color: 0x304b4d, alpha: 0.94 });
  const labels = new Container();
  labels.addChild(namePlate, name, statusPlate, status);
  container.addChild(shadow, body, labels);
  container.position.set(POSITIONS.entrance.x, POSITIONS.entrance.y);
  return {
    container,
    body,
    labels,
    name,
    status,
    path: [],
    targetZone: "entrance",
    targetPoint: POSITIONS.entrance,
    showLabel: true,
    animation: "entering",
    phase: Math.random() * Math.PI * 2,
  };
}

export function OfficeScene({ agents, deskCount, usage = null }: OfficeSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const sceneryRef = useRef<OfficeScenery | null>(null);
  const renderedRef = useRef(new Map<string, RenderedAgent>());
  const assignmentsRef = useRef(new Map<string, string>());
  const [ready, setReady] = useState(false);
  const selectAgent = useAgentStore((state) => state.selectAgent);
  const atmosphere = atmosphereForUsage(usage?.remaining_percent ?? null);
  const atmosphereRef = useRef(atmosphere);
  atmosphereRef.current = atmosphere;

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const app = new Application();
    const renderedAgents = renderedRef.current;
    const deskAssignments = assignmentsRef.current;
    let cancelled = false;
    void app.init({ width: OFFICE_WIDTH, height: OFFICE_HEIGHT, antialias: true, backgroundColor: 0x202d31, resolution: Math.min(window.devicePixelRatio, 2), autoDensity: true }).then(() => {
      if (cancelled) return app.destroy();
      app.canvas.className = "office-canvas";
      app.canvas.style.width = "100%";
      app.canvas.style.height = "100%";
      host.appendChild(app.canvas);
      app.stage.sortableChildren = true;
      sceneryRef.current = drawOfficeScenery(app, atmosphereRef.current);
      appRef.current = app;
      app.ticker.add((ticker) => {
        for (const rendered of renderedAgents.values()) {
          const waypoint = rendered.path[0];
          if (waypoint) {
            const dx = waypoint.x - rendered.container.x;
            const dy = waypoint.y - rendered.container.y;
            const distance = Math.hypot(dx, dy);
            if (distance < 4) rendered.path.shift();
            else {
              const movement = Math.min(distance, ticker.deltaTime * 4.4);
              rendered.container.x += (dx / distance) * movement;
              rendered.container.y += (dy / distance) * movement;
            }
          }
          const time = app.ticker.lastTime / 180 + rendered.phase;
          const active = rendered.animation === "typing" || rendered.animation === "testing" || rendered.animation === "working_machine";
          rendered.body.y = active ? Math.sin(time * 2) * 1.5 : 0;
          rendered.body.rotation = rendered.animation === "celebration" ? Math.sin(time * 2) * 0.12 : 0;
          rendered.body.alpha = rendered.animation === "error" ? 0.65 + Math.sin(time * 3) * 0.3 : 1;
          rendered.labels.visible = rendered.showLabel && rendered.path.length === 0;
          rendered.container.zIndex = 100 + Math.round(rendered.container.y);
        }
        const separated = separateAgentPositions(
          [...renderedAgents].map(([id, rendered]) => ({
            id,
            x: rendered.container.x,
            y: rendered.container.y,
            radius: 25 * rendered.container.scale.x,
          })),
        );
        for (const [id, point] of separated) {
          const rendered = renderedAgents.get(id);
          if (!rendered) continue;
          const current = { x: rendered.container.x, y: rendered.container.y };
          const constrained = [
            point,
            { x: point.x, y: current.y },
            { x: current.x, y: point.y },
          ].find(isOfficePositionWalkable) ?? current;
          rendered.container.position.set(constrained.x, constrained.y);
        }
      });
      setReady(true);
    });
    return () => {
      cancelled = true;
      renderedAgents.clear();
      deskAssignments.clear();
      appRef.current = null;
      sceneryRef.current = null;
      if (app.renderer) app.destroy(true, { children: true });
    };
  }, []);

  useEffect(() => {
    if (ready) sceneryRef.current?.setAtmosphere(atmosphere);
  }, [atmosphere, ready]);

  useEffect(() => {
    const app = appRef.current;
    if (!app || !ready) return;
    const currentIds = new Set(agents.map((agent) => agent.id));
    for (const [agentId, rendered] of renderedRef.current) {
      if (!currentIds.has(agentId)) {
        app.stage.removeChild(rendered.container);
        rendered.container.destroy({ children: true });
        renderedRef.current.delete(agentId);
        assignmentsRef.current.delete(agentId);
      }
    }
    const availableDesks = Math.max(1, Math.min(deskCount, 8));
    const projections = agents.map((agent) => ({
      agent,
      visual: visualFor(agent.status, assignDesk(agent.id, assignmentsRef.current, availableDesks)),
    }));
    const targetPositions = spreadAgentTargets(
      projections.map(({ agent, visual }) => ({ id: agent.id, zone: visual.zone })),
    );

    for (const { agent, visual } of projections) {
      let rendered = renderedRef.current.get(agent.id);
      if (!rendered) {
        rendered = createRenderedAgent(agent, selectAgent);
        renderedRef.current.set(agent.id, rendered);
        app.stage.addChild(rendered.container);
      }
      rendered.name.text = shortName(agent.name);
      rendered.status.text = agent.status.toUpperCase();
      rendered.animation = visual.animation;
      const placement = targetPositions.get(agent.id) ?? {
        ...POSITIONS.entrance,
        scale: 1,
        showLabel: true,
      };
      rendered.container.scale.set(placement.scale);
      rendered.showLabel = placement.showLabel;
      const target = { x: placement.x, y: placement.y };
      if (visual.zone === "entrance" && rendered.targetZone === "entrance") {
        rendered.container.position.set(target.x, target.y);
      }
      if (
        visual.zone !== rendered.targetZone
        || target.x !== rendered.targetPoint.x
        || target.y !== rendered.targetPoint.y
      ) {
        rendered.targetZone = visual.zone;
        rendered.targetPoint = target;
        rendered.path = routeBetween(
          { x: rendered.container.x, y: rendered.container.y },
          target,
        );
      }
    }
  }, [agents, deskCount, ready, selectAgent]);

  return <div className="office-scene" ref={hostRef} aria-label="Live agent office map" />;
}

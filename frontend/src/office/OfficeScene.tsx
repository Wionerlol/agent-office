import { Application, Container, Graphics, Text, TextStyle } from "pixi.js";
import { useEffect, useRef, useState } from "react";

import type { Agent } from "../models/agent";
import { useAgentStore } from "../store/agents";
import { assignDesk, OFFICE_HEIGHT, OFFICE_WIDTH, POSITIONS, ZONES, type Point } from "./layout";
import { routeBetween } from "./navigation";
import { visualFor, type VisualState } from "./visual";

interface OfficeSceneProps {
  agents: Agent[];
  deskCount: number;
}

interface RenderedAgent {
  container: Container;
  body: Graphics;
  name: Text;
  status: Text;
  path: Point[];
  targetZone: string;
  animation: VisualState;
  phase: number;
}

const agentColor = (id: string) => {
  const palette = [0x3a7d78, 0xc46a4a, 0x6e6599, 0x4f789e, 0xa67c3d, 0x987070];
  return palette[[...id].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % palette.length];
};

function drawOffice(app: Application) {
  app.stage.addChild(new Graphics().roundRect(12, 12, OFFICE_WIDTH - 24, OFFICE_HEIGHT - 24, 18).fill(0xe8e2d3));
  for (const zone of ZONES) {
    app.stage.addChild(
      new Graphics()
        .roundRect(zone.x, zone.y, zone.width, zone.height, 14)
        .fill({ color: zone.color, alpha: 0.68 })
        .stroke({ width: 2, color: 0x48595a, alpha: 0.3 }),
    );
    const label = new Text({
      text: zone.label,
      style: new TextStyle({ fontFamily: "monospace", fontSize: 13, fill: 0x364346, fontWeight: "600" }),
    });
    label.position.set(zone.x + 12, zone.y + 10);
    app.stage.addChild(label);
  }
  Object.entries(POSITIONS)
    .filter(([id]) => id.startsWith("desk-"))
    .forEach(([id, point]) => {
      app.stage.addChild(new Graphics().roundRect(point.x - 48, point.y - 24, 96, 48, 8).fill(0x88715a));
      const label = new Text({ text: id.toUpperCase(), style: { fontFamily: "monospace", fontSize: 10, fill: 0xf3ead9 } });
      label.anchor.set(0.5);
      label.position.set(point.x, point.y);
      app.stage.addChild(label);
    });
  const hour = new Date().getHours();
  if (hour < 7 || hour >= 19) {
    app.stage.addChild(new Graphics().roundRect(12, 12, OFFICE_WIDTH - 24, OFFICE_HEIGHT - 24, 18).fill({ color: 0x182a46, alpha: 0.2 }));
  }
  for (const [x, y] of [[158, 26], [798, 446], [1080, 226]]) {
    app.stage.addChild(new Graphics().circle(x, y, 5).fill(0x6d8b72));
  }
}

function createRenderedAgent(agent: Agent, selectAgent: (id: string) => void): RenderedAgent {
  const container = new Container();
  container.eventMode = "static";
  container.cursor = "pointer";
  container.on("pointertap", () => selectAgent(agent.id));
  const shadow = new Graphics().ellipse(0, 19, 22, 8).fill({ color: 0x263236, alpha: 0.25 });
  const body = new Graphics()
    .roundRect(-18, -22, 36, 42, 12)
    .fill(agentColor(agent.id))
    .circle(-7, -5, 2.4)
    .circle(7, -5, 2.4)
    .fill(0xf7ead4);
  const name = new Text({ text: agent.name, style: { fontFamily: "system-ui", fontSize: 13, fill: 0x17262b, fontWeight: "600" } });
  name.anchor.set(0.5);
  name.position.set(0, 32);
  const status = new Text({ text: agent.status, style: { fontFamily: "monospace", fontSize: 10, fill: 0x425457 } });
  status.anchor.set(0.5);
  status.position.set(0, 48);
  container.addChild(shadow, body, name, status);
  container.position.set(POSITIONS.entrance.x, POSITIONS.entrance.y);
  return { container, body, name, status, path: [], targetZone: "entrance", animation: "entering", phase: Math.random() * Math.PI * 2 };
}

export function OfficeScene({ agents, deskCount }: OfficeSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const renderedRef = useRef(new Map<string, RenderedAgent>());
  const assignmentsRef = useRef(new Map<string, string>());
  const [ready, setReady] = useState(false);
  const selectAgent = useAgentStore((state) => state.selectAgent);

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
      host.appendChild(app.canvas);
      drawOffice(app);
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
        }
      });
      setReady(true);
    });
    return () => {
      cancelled = true;
      renderedAgents.clear();
      deskAssignments.clear();
      appRef.current = null;
      if (app.renderer) app.destroy(true, { children: true });
    };
  }, []);

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
    for (const agent of agents) {
      let rendered = renderedRef.current.get(agent.id);
      if (!rendered) {
        rendered = createRenderedAgent(agent, selectAgent);
        renderedRef.current.set(agent.id, rendered);
        app.stage.addChild(rendered.container);
      }
      rendered.name.text = agent.name;
      rendered.status.text = agent.status;
      const availableDesks = Math.max(1, Math.min(deskCount, 8));
      const visual = visualFor(
        agent.status,
        assignDesk(agent.id, assignmentsRef.current, availableDesks),
      );
      rendered.animation = visual.animation;
      if (visual.zone !== rendered.targetZone) {
        rendered.targetZone = visual.zone;
        rendered.path = routeBetween(
          { x: rendered.container.x, y: rendered.container.y },
          POSITIONS[visual.zone] ?? POSITIONS.entrance,
        );
      }
    }
  }, [agents, deskCount, ready, selectAgent]);

  return <div className="office-scene" ref={hostRef} aria-label="Live agent office map" />;
}

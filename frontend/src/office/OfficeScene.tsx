import { Application, Container, Graphics, Text, TextStyle } from "pixi.js";
import { useEffect, useRef } from "react";

import type { Agent } from "../models/agent";
import { useAgentStore } from "../store/agents";
import { deskFor, OFFICE_HEIGHT, OFFICE_WIDTH, POSITIONS, ZONES } from "./layout";
import { visualFor } from "./visual";

interface OfficeSceneProps {
  agents: Agent[];
}

const agentColor = (id: string) => {
  const palette = [0x3a7d78, 0xc46a4a, 0x6e6599, 0x4f789e, 0xa67c3d, 0x987070];
  return palette[[...id].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % palette.length];
};

export function OfficeScene({ agents }: OfficeSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const selectAgent = useAgentStore((state) => state.selectAgent);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const app = new Application();
    let cancelled = false;

    void app.init({
      width: OFFICE_WIDTH,
      height: OFFICE_HEIGHT,
      antialias: true,
      backgroundColor: 0x202d31,
      resolution: Math.min(window.devicePixelRatio, 2),
      autoDensity: true,
    }).then(() => {
      if (cancelled) {
        app.destroy();
        return;
      }
      app.canvas.className = "office-canvas";
      host.appendChild(app.canvas);

      const floor = new Graphics().roundRect(12, 12, OFFICE_WIDTH - 24, OFFICE_HEIGHT - 24, 18).fill(0xe8e2d3);
      app.stage.addChild(floor);

      for (const zone of ZONES) {
        const shape = new Graphics()
          .roundRect(zone.x, zone.y, zone.width, zone.height, 14)
          .fill({ color: zone.color, alpha: 0.68 })
          .stroke({ width: 2, color: 0x48595a, alpha: 0.3 });
        app.stage.addChild(shape);
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
          const desk = new Graphics().roundRect(point.x - 48, point.y - 24, 96, 48, 8).fill(0x88715a);
          app.stage.addChild(desk);
          const label = new Text({
            text: id.toUpperCase(),
            style: { fontFamily: "monospace", fontSize: 10, fill: 0xf3ead9 },
          });
          label.anchor.set(0.5);
          label.position.set(point.x, point.y);
          app.stage.addChild(label);
        });

      for (const [index, agent] of agents.entries()) {
        const visual = visualFor(agent.status, deskFor(agent.id));
        const target = POSITIONS[visual.zone] ?? POSITIONS.entrance;
        const sprite = new Container();
        sprite.eventMode = "static";
        sprite.cursor = "pointer";
        sprite.on("pointertap", () => selectAgent(agent.id));

        const shadow = new Graphics().ellipse(0, 19, 22, 8).fill({ color: 0x263236, alpha: 0.25 });
        const body = new Graphics()
          .roundRect(-18, -22, 36, 42, 12)
          .fill(agentColor(agent.id))
          .circle(-7, -5, 2.4)
          .circle(7, -5, 2.4)
          .fill(0xf7ead4);
        sprite.addChild(shadow, body);

        const name = new Text({ text: agent.name, style: { fontFamily: "system-ui", fontSize: 13, fill: 0x17262b, fontWeight: "600" } });
        name.anchor.set(0.5);
        name.position.set(0, 32);
        const status = new Text({ text: agent.status, style: { fontFamily: "monospace", fontSize: 10, fill: 0x425457 } });
        status.anchor.set(0.5);
        status.position.set(0, 48);
        sprite.addChild(name, status);

        sprite.position.set(POSITIONS.entrance.x, POSITIONS.entrance.y + index * 3);
        app.stage.addChild(sprite);
        app.ticker.add((ticker) => {
          const ease = Math.min(1, ticker.deltaTime * 0.055);
          sprite.x += (target.x - sprite.x) * ease;
          sprite.y += (target.y - sprite.y) * ease;
          const pulse = visual.animation === "error" ? Math.sin(app.ticker.lastTime / 90) * 0.08 : 0;
          sprite.scale.set(1 + pulse);
        });
      }
    });

    return () => {
      cancelled = true;
      if (app.renderer) app.destroy(true, { children: true });
    };
  }, [agents, selectAgent]);

  return <div className="office-scene" ref={hostRef} aria-label="Live agent office map" />;
}

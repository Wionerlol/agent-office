import { Application, Container, Graphics, Rectangle, Text } from "pixi.js";
import { useEffect, useRef, useState } from "react";

import type { Agent, CodexUsage } from "../models/agent";
import { useAgentStore } from "../store/agents";
import { atmosphereForUsage } from "./atmosphere";
import { assignDesk, OFFICE_HEIGHT, OFFICE_WIDTH, POSITIONS, separateAgentPositions, StableZoneSlots, type Point } from "./layout";
import { isOfficePositionWalkable, routeBetween } from "./navigation";
import { drawOfficeScenery, type OfficeScenery } from "./scenery";
import { spatialBehaviorFor, type VisualState } from "./visual";

import type { InteractionCue } from "../models/interaction";
import { InteractionLayer } from "./interactions";

import { focusFor, identitySummary, officeDescription, type AgentFocus } from "./focus";
import { placeLabels } from "./readability";
import { bodyPose } from "./motion";

interface OfficeSceneProps {
  agents: Agent[];
  deskCount: number;
  usage?: CodexUsage | null;
  cues?: readonly InteractionCue[];
  selectedId?: string | null;
  reducedMotion?: boolean;
}

interface RenderedAgent {
  container: Container;
  body: Container;
  labels: Container;
  namePlate: Graphics;
  statusPlate: Graphics;
  ring: Graphics;
  focus?: AgentFocus;
  labelWidth: number;
  labelHeight: number;
  presentationKey?: string;
  name: Text;
  status: Text;
  indicator: Container;
  indicatorText: Text;
  indicatorPlate: Graphics;
  path: Point[];
  targetZone: string;
  targetPoint: Point;
  showLabel: boolean;
  animation: VisualState;
  phase: number;
  distanceBefore: number;
  stalledFrames: number;
  holdPosition: boolean;
}

const agentColor = (id: string): number => {
  const palette = [0x3a7d78, 0xc46a4a, 0x6e6599, 0x4f789e, 0xa67c3d, 0x987070];
  return palette[[...id].reduce((sum, letter) => sum + letter.charCodeAt(0), 0) % palette.length];
};

const shortName = (name: string): string => name.length > 15 ? `${name.slice(0, 13)}…` : name;

function createRenderedAgent(agent: Agent, selectAgent: (id: string) => void, hoverAgent: (id: string | null) => void): RenderedAgent {
  const container = new Container();
  container.eventMode = "static";
  container.cursor = "pointer";
  container.on("pointertap", (event) => { event.stopPropagation(); selectAgent(agent.id); });
  container.on("pointerover", () => hoverAgent(agent.id));
  container.on("pointerout", () => hoverAgent(null));
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
  const indicatorText = new Text({ text: "", style: { fontFamily: "system-ui", fontSize: 11, fill: 0x263234, fontWeight: "700" } });
  indicatorText.anchor.set(0.5);
  const indicator = new Container();
  indicator.position.set(0, -62);
  const indicatorPlate = new Graphics();
  indicator.addChild(indicatorPlate, indicatorText);
  indicator.visible = false;
  const ring = new Graphics();
  container.addChild(shadow, ring, body, indicator);
  labels.label = `agent-labels:${agent.id}`;
  labels.eventMode = "none";
  container.position.set(POSITIONS.entrance.x, POSITIONS.entrance.y);
  return {
    container,
    body,
    labels,
    namePlate, statusPlate, ring, labelWidth: 100, labelHeight: 36,
    name,
    status,
    indicator,
    indicatorText,
    indicatorPlate,
    path: [],
    targetZone: "entrance",
    targetPoint: POSITIONS.entrance,
    showLabel: true,
    animation: "entering",
    phase: Math.random() * Math.PI * 2,
    distanceBefore: Infinity,
    stalledFrames: 0,
    holdPosition: false,
  };
}

export function OfficeScene({ agents, deskCount, usage = null, cues = [], selectedId = null, reducedMotion = false }: OfficeSceneProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const interactionsRef = useRef<InteractionLayer | null>(null);
  const appRef = useRef<Application | null>(null);
  const sceneryRef = useRef<OfficeScenery | null>(null);
  const renderedRef = useRef(new Map<string, RenderedAgent>());
  const assignmentsRef = useRef(new Map<string, string>());
  const slotsRef = useRef(new StableZoneSlots());
  const [ready, setReady] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const presentationRef = useRef({ reducedMotion });
  presentationRef.current = { reducedMotion };
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
    const slots = slotsRef.current;
    let cancelled = false;
    void app.init({ width: OFFICE_WIDTH, height: OFFICE_HEIGHT, antialias: true, backgroundColor: 0x202d31, resolution: Math.min(window.devicePixelRatio, 2), autoDensity: true }).then(() => {
      if (cancelled) return app.destroy();
      app.canvas.className = "office-canvas";
      app.canvas.style.width = "100%";
      app.canvas.style.height = "100%";
      host.appendChild(app.canvas);
      app.stage.sortableChildren = true;
      app.stage.eventMode = "static";
      app.stage.hitArea = new Rectangle(0, 0, OFFICE_WIDTH, OFFICE_HEIGHT);
      app.stage.on("pointertap", () => useAgentStore.getState().selectAgent(null));
      sceneryRef.current = drawOfficeScenery(app, atmosphereRef.current);
      // Background/furniture never intercept actor hover/taps when the stage handles empty taps.
      for (const child of app.stage.children) child.eventMode = "none";
      appRef.current = app;
      interactionsRef.current = new InteractionLayer(app.stage);
      let movementFrames = 0;
      app.ticker.add((ticker) => {
        // Fixed movement steps make collision resolution independent of render frame timing.
        // Bound catch-up after a background-tab pause instead of teleporting through furniture.
        movementFrames = Math.min(movementFrames + ticker.deltaTime, 6);
        while (movementFrames >= 1) {
          movementFrames -= 1;
          for (const rendered of renderedAgents.values()) {
            const waypoint = rendered.path[0];
            if (waypoint) {
              const dx = waypoint.x - rendered.container.x;
              const dy = waypoint.y - rendered.container.y;
              const distance = Math.hypot(dx, dy);
              rendered.distanceBefore = distance;
              if (distance < 4) rendered.path.shift();
              else {
                const movement = Math.min(distance, presentationRef.current.reducedMotion ? 12 : 4.4);
                rendered.container.x += (dx / distance) * movement;
                rendered.container.y += (dy / distance) * movement;
              }
            }
            const time = app.ticker.lastTime / 180 + rendered.phase;
            const pose = bodyPose(rendered.animation, time, presentationRef.current.reducedMotion);
            rendered.body.y = pose.y;
            rendered.body.rotation = pose.rotation;
            rendered.body.alpha = pose.alpha;
            rendered.indicator.alpha = pose.attentionAlpha;
            rendered.container.zIndex = 100 + Math.round(rendered.container.y);
          }
          const separated = separateAgentPositions(
            [...renderedAgents].map(([id, rendered]) => ({
              id,
              x: rendered.container.x,
              y: rendered.container.y,
              // Doorways admit a moving figure, while settled figures keep their full seat space.
              radius: (rendered.path.length ? 16 : 25) * rendered.container.scale.x,
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
            const waypoint = rendered.path[0];
            if (waypoint) {
              const remaining = Math.hypot(waypoint.x - constrained.x, waypoint.y - constrained.y);
              rendered.stalledFrames = rendered.distanceBefore - remaining > 0.25
                ? 0 : rendered.stalledFrames + 1;
              if (rendered.stalledFrames >= 60) {
                // Collision avoidance can displace a walker to the other side of furniture.
                // Refresh only stalled routes, preserving stable destinations and the same grid.
                const refreshed = routeBetween(constrained, rendered.targetPoint);
                if (refreshed.length) rendered.path = refreshed;
                rendered.stalledFrames = 0;
              }
            } else {
              rendered.stalledFrames = 0;
              // A passing walker must not permanently displace a settled character from its seat.
              if (!rendered.holdPosition && Math.hypot(constrained.x - rendered.targetPoint.x, constrained.y - rendered.targetPoint.y) > 12) {
                rendered.path = routeBetween(constrained, rendered.targetPoint);
              }
            }
          }
        }
        const labelPositions = placeLabels([...renderedAgents].map(([id, r]) => ({
          id, x: r.container.x, y: r.container.y + 27 * r.container.scale.x + r.labelHeight / 2,
          width: r.labelWidth, height: r.labelHeight, priority: r.focus?.priority ?? 1,
          eligible: Boolean(r.focus?.importantLabel || (r.showLabel && (!r.path.length || r.animation === "celebration"))),
        })));
        for (const [id, r] of renderedAgents) {
          const point = labelPositions.get(id);
          r.labels.visible = Boolean(point);
          if (point) r.labels.position.set(point.x, point.y - (27 + r.labelHeight / 2));
        }
        interactionsRef.current?.draw(new Map([...renderedAgents].map(([id, r]) => [id, {
          x: r.container.x, y: r.container.y, scale: r.container.scale.x,
        }])), Date.now());
      });
      setReady(true);
    });
    return () => {
      cancelled = true;
      interactionsRef.current?.destroy();
      interactionsRef.current = null;
      for (const r of renderedAgents.values()) {
        r.container.destroy({ children: true });
        r.labels.destroy({ children: true });
      }
      renderedAgents.clear();
      deskAssignments.clear();
      slots.clear();
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
        rendered.labels.destroy({ children: true });
        renderedRef.current.delete(agentId);
        assignmentsRef.current.delete(agentId);
      }
    }
    const availableDesks = Math.max(1, Math.min(deskCount, 8));
    const projections = agents.map((agent) => ({
      agent,
      visual: spatialBehaviorFor(agent, assignDesk(agent.id, assignmentsRef.current, availableDesks)),
    }));
    const targetPositions = slotsRef.current.place(
      projections.map(({ agent, visual }) => ({
        id: agent.id,
        zone: visual.holdPosition ? renderedRef.current.get(agent.id)?.targetZone ?? visual.destinationZone : visual.destinationZone,
      })),
    );

    for (const { agent, visual } of projections) {
      let rendered = renderedRef.current.get(agent.id);
      const newlyCreated = !rendered;
      if (!rendered) {
        rendered = createRenderedAgent(agent, selectAgent, setHoveredId);
        renderedRef.current.set(agent.id, rendered);
        app.stage.addChild(rendered.container, rendered.labels);
      }
      rendered.animation = visual.animation;
      rendered.holdPosition = visual.holdPosition;
      const compactAttention = visual.attention === "user";
      const indicatorText = compactAttention ? "?" : visual.indicator ?? "";
      if (rendered.indicatorText.text !== indicatorText) {
        const halfWidth = compactAttention ? 12 : 47;
        rendered.indicatorText.text = indicatorText;
        rendered.indicatorPlate.clear().roundRect(-halfWidth, -10, halfWidth * 2, 20, 7)
          .fill(0xffe6ae).stroke({ width: 1, color: 0x826539 });
      }
      rendered.indicator.position.set(compactAttention ? 30 : 0, compactAttention ? -30 : -62);
      rendered.indicator.visible = visual.indicator !== null;
      const placement = targetPositions.get(agent.id) ?? {
        ...POSITIONS.entrance,
        scale: 1,
        showLabel: true,
      };
      rendered.container.scale.set(placement.scale);
      rendered.showLabel = placement.showLabel;
      const target = { x: placement.x, y: placement.y };
      if (visual.holdPosition) {
        if (newlyCreated) {
          rendered.container.position.set(target.x, target.y);
          rendered.targetZone = visual.destinationZone;
          rendered.targetPoint = target;
        }
        rendered.path = [];
        rendered.stalledFrames = 0;
        continue;
      }
      if (visual.destinationZone === "entrance" && rendered.targetZone === "entrance") {
        rendered.container.position.set(target.x, target.y);
      }
      if (
        visual.destinationZone !== rendered.targetZone
        || target.x !== rendered.targetPoint.x
        || target.y !== rendered.targetPoint.y
      ) {
        rendered.targetZone = visual.destinationZone;
        rendered.targetPoint = target;
        rendered.stalledFrames = 0;
        rendered.path = routeBetween(
          { x: rendered.container.x, y: rendered.container.y },
          target,
        );
      }
    }
  }, [agents, deskCount, ready, selectAgent]);

  useEffect(() => {
    interactionsRef.current?.setState(agents, cues);
  }, [agents, cues, ready]);

  // Presentation updates are deliberately separate from seat assignment and route updates.
  useEffect(() => {
    const focus = focusFor(agents, selectedId, hoveredId, cues, Date.now());
    for (const agent of agents) {
      const rendered = renderedRef.current.get(agent.id), projection = focus.get(agent.id);
      if (!rendered || !projection) continue;
      rendered.focus = projection;
      const key = JSON.stringify([agent.name, agent.role, agent.status, projection.selected, projection.related,
        projection.dimmed, projection.priority, projection.expandedLabel, rendered.container.scale.x]);
      if (rendered.presentationKey === key) continue;
      rendered.presentationKey = key;
      rendered.container.alpha = projection.dimmed ? 0.62 : 1;
      rendered.labels.alpha = projection.dimmed ? 0.7 : 1;
      rendered.labels.zIndex = 1000 + projection.priority;
      rendered.ring.clear();
      if (projection.selected || projection.related) rendered.ring.ellipse(0, 18, projection.selected ? 29 : 26, 10)
        .stroke({ color: projection.selected ? 0x244c60 : 0x6b837e, width: projection.selected ? 3 : 1.5, alpha: 0.9 });
      rendered.name.text = projection.expandedLabel ? agent.name : shortName(agent.name);
      rendered.status.text = projection.expandedLabel ? identitySummary(agent) : agent.status.toUpperCase();
      // Fixed screen-space plates remain readable even when dense physical slots shrink actors.
      for (const text of [rendered.name, rendered.status]) {
        text.style.wordWrap = true;
        text.style.wordWrapWidth = 344;
        text.style.breakWords = true;
      }
      rendered.labelWidth = Math.min(360, Math.max(100, rendered.name.width + 16, rendered.status.width + 16));
      const nameHeight = Math.max(21, rendered.name.height + 6), statusHeight = Math.max(14, rendered.status.height + 4);
      rendered.labelHeight = nameHeight + statusHeight;
      rendered.name.position.set(0, 27 + nameHeight / 2);
      rendered.status.position.set(0, 27 + nameHeight + statusHeight / 2);
      rendered.namePlate.clear().roundRect(-rendered.labelWidth / 2, 27, rendered.labelWidth, nameHeight, 7)
        .fill({ color: projection.selected ? 0xffefc8 : 0xf8f2e6, alpha: 0.97 })
        .stroke({ color: 0x314649, width: projection.selected ? 2 : 1, alpha: 0.6 });
      rendered.statusPlate.clear().roundRect(-rendered.labelWidth / 2, 27 + nameHeight, rendered.labelWidth, statusHeight, 6).fill(0x304b4d);
      rendered.indicator.scale.set(projection.importantLabel ? 1 / rendered.container.scale.x : 1);
    }
    interactionsRef.current?.setPresentation(selectedId, focus, reducedMotion);
  }, [agents, cues, selectedId, hoveredId, reducedMotion, ready]);

  return <div className="office-scene" ref={hostRef} role="img" aria-label={officeDescription(agents, selectedId)} />;
}

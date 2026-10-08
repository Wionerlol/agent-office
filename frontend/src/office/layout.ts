export interface Point {
  x: number;
  y: number;
}

export interface ZoneLayout {
  id: string;
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color: number;
}

export interface AgentTarget {
  id: string;
  zone: string;
}

export interface AgentPlacement extends Point {
  scale: number;
  showLabel: boolean;
}

export const OFFICE_WIDTH = 1100;
export const OFFICE_HEIGHT = 680;

export const ZONES: ZoneLayout[] = [
  { id: "entrance", label: "RECEPTION", x: 28, y: 280, width: 118, height: 110, color: 0xc5d5ca },
  { id: "review_area", label: "REVIEW", x: 28, y: 42, width: 118, height: 206, color: 0xcbb8c3 },
  { id: "user_attention", label: "NEEDS YOU", x: 28, y: 420, width: 118, height: 222, color: 0xe5c38a },
  { id: "desk_area", label: "OPEN OFFICE", x: 176, y: 42, width: 610, height: 388, color: 0xded4c1 },
  { id: "library", label: "RESEARCH LIBRARY", x: 816, y: 42, width: 254, height: 170, color: 0xd8c9a8 },
  { id: "coffee_area", label: "CAFÉ & KITCHEN", x: 176, y: 462, width: 182, height: 180, color: 0xc8ad8d },
  { id: "lounge", label: "TEAM LOUNGE", x: 382, y: 462, width: 192, height: 180, color: 0xcbb8c3 },
  { id: "tool_lab", label: "BUILD LAB", x: 598, y: 462, width: 214, height: 180, color: 0xadc2c1 },
  { id: "test_lab", label: "QA LAB", x: 836, y: 246, width: 234, height: 246, color: 0xadc0a8 },
  { id: "exit", label: "EXIT", x: 912, y: 536, width: 158, height: 106, color: 0xc49b8c },
];

export const POSITIONS: Record<string, Point> = {
  entrance: { x: 85, y: 370 },
  review_area: { x: 87, y: 156 },
  user_attention: { x: 87, y: 532 },
  coordination: { x: 477, y: 558 },
  "desk-1": { x: 250, y: 230 },
  "desk-2": { x: 400, y: 230 },
  "desk-3": { x: 550, y: 230 },
  "desk-4": { x: 700, y: 230 },
  "desk-5": { x: 250, y: 370 },
  "desk-6": { x: 400, y: 370 },
  "desk-7": { x: 550, y: 370 },
  "desk-8": { x: 700, y: 370 },
  library: { x: 942, y: 169 },
  coffee_area: { x: 275, y: 558 },
  lounge: { x: 477, y: 558 },
  tool_lab: { x: 705, y: 575 },
  test_lab: { x: 952, y: 370 },
  exit: { x: 992, y: 588 },
};

interface PlacementArea {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface GridLayout {
  columns: number;
  rows: number;
  scale: number;
  gapX: number;
  gapY: number;
  itemWidth: number;
  itemHeight: number;
}

const ZONE_PLACEMENT_AREAS: Record<string, PlacementArea> = {
  entrance: { x: 36, y: 355, width: 102, height: 27 },
  library: { x: 824, y: 120, width: 238, height: 84 },
  coffee_area: { x: 184, y: 535, width: 166, height: 99 },
  lounge: { x: 390, y: 544, width: 176, height: 37 },
  tool_lab: { x: 606, y: 560, width: 198, height: 74 },
  test_lab: { x: 844, y: 344, width: 218, height: 52 },
  exit: { x: 920, y: 544, width: 142, height: 90 },
};

function placementArea(zone: string, anchor: Point): PlacementArea {
  if (zone.startsWith("desk-")) return { x: anchor.x - 56, y: anchor.y + 10, width: 112, height: 32 };
  const room = ZONES.find((candidate) => candidate.id === zone);
  if (!room) return { x: anchor.x - 62, y: anchor.y - 58, width: 124, height: 116 };
  if (ZONE_PLACEMENT_AREAS[zone]) return ZONE_PLACEMENT_AREAS[zone];
  return {
    x: room.x + 8,
    y: room.y + 32,
    width: room.width - 16,
    height: room.height - 40,
  };
}

function bestGrid(count: number, area: PlacementArea, showLabel: boolean): GridLayout {
  const itemWidth = showLabel ? 96 : 46;
  const itemHeight = showLabel ? 108 : 69;
  const baseGapX = showLabel ? 100 : 50;
  const baseGapY = showLabel ? 110 : 72;
  let best: GridLayout | undefined;
  for (let columns = 1; columns <= count; columns += 1) {
    const rows = Math.ceil(count / columns);
    const unscaledWidth = (Math.min(columns, count) - 1) * baseGapX + itemWidth;
    const unscaledHeight = (rows - 1) * baseGapY + itemHeight;
    const scale = Math.min(1, area.width / unscaledWidth, area.height / unscaledHeight);
    if (!best || scale > best.scale) {
      best = {
        columns,
        rows,
        scale,
        gapX: baseGapX * scale,
        gapY: baseGapY * scale,
        itemWidth: itemWidth * scale,
        itemHeight: itemHeight * scale,
      };
    }
  }
  return best!;
}

function spreadAround(anchor: Point, count: number, zone: string): AgentPlacement[] {
  const area = placementArea(zone, anchor);
  const labeled = bestGrid(count, area, true);
  const showLabel = count <= 3 && labeled.scale >= 0.7;
  const grid = showLabel ? labeled : bestGrid(count, area, false);
  const occupiedWidth = (Math.min(grid.columns, count) - 1) * grid.gapX + grid.itemWidth;
  const occupiedHeight = (grid.rows - 1) * grid.gapY + grid.itemHeight;
  const centerX = Math.max(
    area.x + occupiedWidth / 2,
    Math.min(anchor.x, area.x + area.width - occupiedWidth / 2),
  );
  const centerY = Math.max(
    area.y + occupiedHeight / 2,
    Math.min(anchor.y, area.y + area.height - occupiedHeight / 2),
  );
  return Array.from({ length: count }, (_, index) => {
    const row = Math.floor(index / grid.columns);
    const itemsInRow = Math.min(grid.columns, count - row * grid.columns);
    const column = index % grid.columns;
    return {
      x: centerX + (column - (itemsInRow - 1) / 2) * grid.gapX,
      y: centerY + (row - (grid.rows - 1) / 2) * grid.gapY,
      scale: grid.scale,
      showLabel,
    };
  });
}

export function spreadAgentTargets(targets: readonly AgentTarget[]): Map<string, AgentPlacement> {
  const byZone = new Map<string, string[]>();
  for (const target of targets) {
    const occupants = byZone.get(target.zone) ?? [];
    occupants.push(target.id);
    byZone.set(target.zone, occupants);
  }

  const positions = new Map<string, AgentPlacement>();
  for (const [zone, occupantIds] of byZone) {
    const anchor = POSITIONS[zone] ?? POSITIONS.entrance;
    const sortedIds = [...occupantIds].sort((left, right) => left.localeCompare(right));
    const slots = spreadAround(anchor, sortedIds.length, zone);
    sortedIds.forEach((id, index) => positions.set(id, slots[index]));
  }
  return positions;
}

// Comfortable, walkable seats use the existing floor/furniture rather than another layout engine.
const TEAM_SLOTS: Record<string, AgentPlacement[]> = {
  library: [865, 943, 1021].map((x) => ({ x, y: 170, scale: 0.75, showLabel: true })),
  test_lab: [371, 470].flatMap((y) => [891, 1007].map((x) => ({ x, y, scale: 0.8, showLabel: true }))),
  review_area: [132, 224].map((y) => ({ x: 87, y, scale: 0.8, showLabel: true })),
  user_attention: [462, 541, 620].map((y) => ({ x: 87, y, scale: 0.72, showLabel: true })),
  lounge: [433, 521].map((x) => ({ x, y: 561, scale: 0.8, showLabel: true })),
  tool_lab: [636, 705, 774].map((x) => ({ x, y: 575, scale: 0.7, showLabel: true })),
};

/** Reservations live only for visible agents. Removing/reordering peers never compacts seats. */
export class StableZoneSlots {
  private reservations = new Map<string, { zone: string; slot: number }>();
  private capacities = new Map<string, number>();

  clear(): void {
    this.reservations.clear();
    this.capacities.clear();
  }

  place(targets: readonly AgentTarget[]): Map<string, AgentPlacement> {
    // Coordination shares the lounge floor, so generic waiting cannot claim the same seat.
    const canonical = targets.map(({ id, zone }) => ({ id, zone: zone === "coordination" ? "lounge" : zone }));
    const current = new Map(canonical.map(({ id, zone }) => [id, zone]));
    for (const [id, reserved] of this.reservations) {
      if (current.get(id) !== reserved.zone) this.reservations.delete(id);
    }
    for (const zone of this.capacities.keys()) {
      if (!canonical.some((target) => target.zone === zone)) this.capacities.delete(zone);
    }
    const result = new Map<string, AgentPlacement>();
    const byZone = new Map<string, string[]>();
    for (const { id, zone } of canonical) byZone.set(zone, [...(byZone.get(zone) ?? []), id]);
    for (const [zone, ids] of byZone) {
      const anchor = POSITIONS[zone] ?? POSITIONS.entrance;
      const comfortable = TEAM_SLOTS[zone] ?? (zone.startsWith("desk-")
        ? [{ x: anchor.x, y: anchor.y + 14, scale: 1, showLabel: true }] : undefined);
      let capacity = this.capacities.get(zone) ?? comfortable?.length ?? 1;
      // Only a meaningful crowding increase repacks a zone; it never shrinks on rerenders/exits.
      while (capacity < ids.length) capacity *= 2;
      this.capacities.set(zone, capacity);
      const seats = comfortable && capacity === comfortable.length
        ? comfortable : spreadAround(POSITIONS[zone] ?? POSITIONS.entrance, capacity, zone);
      const taken = new Set([...this.reservations.values()].filter((r) => r.zone === zone).map((r) => r.slot));
      for (const id of [...ids].sort()) {
        let reservation = this.reservations.get(id);
        if (!reservation) {
          let slot = 0;
          while (taken.has(slot)) slot += 1;
          reservation = { zone, slot };
          this.reservations.set(id, reservation);
          taken.add(slot);
        }
        result.set(id, seats[reservation.slot]);
      }
    }
    return result;
  }
}

export function separateAgentPositions(
  agents: readonly (Point & { id: string; radius?: number })[],
  minimumDistance = 50,
): Map<string, Point> {
  const radii = new Map(agents.map(({ id, radius }) => [id, radius ?? minimumDistance / 2]));
  const positions = new Map(
    [...agents]
      .sort((left, right) => left.id.localeCompare(right.id))
      .map(({ id, x, y }) => [id, { x, y }]),
  );
  const ids = [...positions.keys()];
  const maximumPasses = Math.max(16, ids.length * 4);
  for (let pass = 0; pass < maximumPasses; pass += 1) {
    let foundOverlap = false;
    for (let left = 0; left < ids.length; left += 1) {
      for (let right = left + 1; right < ids.length; right += 1) {
        const first = positions.get(ids[left])!;
        const second = positions.get(ids[right])!;
        let deltaX = second.x - first.x;
        let deltaY = second.y - first.y;
        let distance = Math.hypot(deltaX, deltaY);
        const requiredDistance = radii.get(ids[left])! + radii.get(ids[right])!;
        if (distance >= requiredDistance) continue;
        foundOverlap = true;
        if (distance === 0) {
          const angle = ((left * ids.length + right) * 2.399963) % (Math.PI * 2);
          deltaX = Math.cos(angle);
          deltaY = Math.sin(angle);
          distance = 1;
        }
        const correction = (requiredDistance - distance) / 2;
        const offsetX = (deltaX / distance) * correction;
        const offsetY = (deltaY / distance) * correction;
        const firstRadius = radii.get(ids[left])!;
        const secondRadius = radii.get(ids[right])!;
        positions.set(ids[left], {
          x: Math.max(24 + firstRadius, Math.min(1076 - firstRadius, first.x - offsetX)),
          y: Math.max(48 + firstRadius, Math.min(650 - firstRadius, first.y - offsetY)),
        });
        positions.set(ids[right], {
          x: Math.max(24 + secondRadius, Math.min(1076 - secondRadius, second.x + offsetX)),
          y: Math.max(48 + secondRadius, Math.min(650 - secondRadius, second.y + offsetY)),
        });
      }
    }
    if (!foundOverlap) break;
  }
  return positions;
}

export function assignDesk(
  agentId: string,
  assignments: Map<string, string>,
  deskCount = 8,
): string {
  const existing = assignments.get(agentId);
  const desks = Array.from({ length: deskCount }, (_, index) => `desk-${index + 1}`);
  if (existing && desks.includes(existing)) return existing;
  const occupancy = new Map(desks.map((desk) => [desk, 0]));
  for (const desk of assignments.values()) {
    occupancy.set(desk, (occupancy.get(desk) ?? 0) + 1);
  }
  const desk = desks.reduce((best, candidate) =>
    (occupancy.get(candidate) ?? 0) < (occupancy.get(best) ?? 0) ? candidate : best,
  );
  assignments.set(agentId, desk);
  return desk;
}

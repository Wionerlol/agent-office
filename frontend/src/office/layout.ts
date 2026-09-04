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

export const OFFICE_WIDTH = 1100;
export const OFFICE_HEIGHT = 680;

export const ZONES: ZoneLayout[] = [
  { id: "entrance", label: "RECEPTION", x: 28, y: 280, width: 118, height: 110, color: 0xc5d5ca },
  { id: "desk_area", label: "OPEN OFFICE", x: 176, y: 42, width: 610, height: 388, color: 0xded4c1 },
  { id: "library", label: "RESEARCH LIBRARY", x: 816, y: 42, width: 254, height: 170, color: 0xd8c9a8 },
  { id: "coffee_area", label: "CAFÉ & KITCHEN", x: 176, y: 462, width: 182, height: 180, color: 0xc8ad8d },
  { id: "lounge", label: "TEAM LOUNGE", x: 382, y: 462, width: 192, height: 180, color: 0xcbb8c3 },
  { id: "tool_lab", label: "BUILD LAB", x: 598, y: 462, width: 214, height: 180, color: 0xadc2c1 },
  { id: "test_lab", label: "QA LAB", x: 836, y: 246, width: 234, height: 246, color: 0xadc0a8 },
  { id: "exit", label: "EXIT", x: 912, y: 536, width: 158, height: 106, color: 0xc49b8c },
];

export const POSITIONS: Record<string, Point> = {
  entrance: { x: 85, y: 340 },
  "desk-1": { x: 250, y: 160 },
  "desk-2": { x: 400, y: 160 },
  "desk-3": { x: 550, y: 160 },
  "desk-4": { x: 700, y: 160 },
  "desk-5": { x: 250, y: 330 },
  "desk-6": { x: 400, y: 330 },
  "desk-7": { x: 550, y: 330 },
  "desk-8": { x: 700, y: 330 },
  library: { x: 942, y: 169 },
  coffee_area: { x: 275, y: 558 },
  lounge: { x: 477, y: 558 },
  tool_lab: { x: 705, y: 575 },
  test_lab: { x: 952, y: 370 },
  exit: { x: 992, y: 588 },
};

const SPREAD_BY_ZONE: Record<string, { columns: number; gapX: number; gapY: number }> = {
  entrance: { columns: 2, gapX: 100, gapY: 110 },
  library: { columns: 3, gapX: 100, gapY: 110 },
  coffee_area: { columns: 3, gapX: 100, gapY: 110 },
  lounge: { columns: 3, gapX: 100, gapY: 110 },
  tool_lab: { columns: 3, gapX: 100, gapY: 110 },
  test_lab: { columns: 3, gapX: 100, gapY: 110 },
  exit: { columns: 2, gapX: 100, gapY: 110 },
};

function spreadAround(anchor: Point, count: number, zone: string): Point[] {
  const config = SPREAD_BY_ZONE[zone] ?? { columns: 2, gapX: 100, gapY: 110 };
  const columns = Math.min(config.columns, count);
  const rows = Math.ceil(count / columns);
  return Array.from({ length: count }, (_, index) => {
    const row = Math.floor(index / columns);
    const itemsInRow = Math.min(columns, count - row * columns);
    const column = index % columns;
    return {
      x: anchor.x + (column - (itemsInRow - 1) / 2) * config.gapX,
      y: anchor.y + (row - (rows - 1) / 2) * config.gapY,
    };
  });
}

export function spreadAgentTargets(targets: readonly AgentTarget[]): Map<string, Point> {
  const byZone = new Map<string, string[]>();
  for (const target of targets) {
    const occupants = byZone.get(target.zone) ?? [];
    occupants.push(target.id);
    byZone.set(target.zone, occupants);
  }

  const positions = new Map<string, Point>();
  for (const [zone, occupantIds] of byZone) {
    const anchor = POSITIONS[zone] ?? POSITIONS.entrance;
    const sortedIds = [...occupantIds].sort((left, right) => left.localeCompare(right));
    const slots = spreadAround(anchor, sortedIds.length, zone);
    sortedIds.forEach((id, index) => positions.set(id, slots[index]));
  }
  return positions;
}

export function separateAgentPositions(
  agents: readonly (Point & { id: string })[],
  minimumDistance = 50,
): Map<string, Point> {
  const positions = new Map(
    [...agents]
      .sort((left, right) => left.id.localeCompare(right.id))
      .map(({ id, x, y }) => [id, { x, y }]),
  );
  const ids = [...positions.keys()];
  const maximumPasses = Math.max(12, ids.length * 8);
  for (let pass = 0; pass < maximumPasses; pass += 1) {
    let foundOverlap = false;
    for (let left = 0; left < ids.length; left += 1) {
      for (let right = left + 1; right < ids.length; right += 1) {
        const first = positions.get(ids[left])!;
        const second = positions.get(ids[right])!;
        let deltaX = second.x - first.x;
        let deltaY = second.y - first.y;
        let distance = Math.hypot(deltaX, deltaY);
        if (distance >= minimumDistance) continue;
        foundOverlap = true;
        if (distance === 0) {
          deltaX = 1;
          deltaY = 0;
          distance = 1;
        }
        const correction = (minimumDistance - distance) / 2;
        const offsetX = (deltaX / distance) * correction;
        const offsetY = (deltaY / distance) * correction;
        positions.set(ids[left], { x: first.x - offsetX, y: first.y - offsetY });
        positions.set(ids[right], { x: second.x + offsetX, y: second.y + offsetY });
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

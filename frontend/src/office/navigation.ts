import { POSITIONS, type Point } from "./layout";

export interface GridPoint {
  x: number;
  y: number;
}

const key = (point: GridPoint) => `${point.x},${point.y}`;
const distance = (a: GridPoint, b: GridPoint) => Math.abs(a.x - b.x) + Math.abs(a.y - b.y);

export function findPath(
  start: GridPoint,
  goal: GridPoint,
  blocked: Set<string>,
  width: number,
  height: number,
): GridPoint[] {
  const open: GridPoint[] = [start];
  const cameFrom = new Map<string, GridPoint>();
  const cost = new Map<string, number>([[key(start), 0]]);
  const visited = new Set<string>();

  while (open.length) {
    open.sort((a, b) => {
      const scoreA = (cost.get(key(a)) ?? Infinity) + distance(a, goal);
      const scoreB = (cost.get(key(b)) ?? Infinity) + distance(b, goal);
      return scoreA - scoreB;
    });
    const current = open.shift()!;
    if (key(current) === key(goal)) {
      const path = [current];
      let cursor = current;
      while (cameFrom.has(key(cursor))) {
        cursor = cameFrom.get(key(cursor))!;
        path.unshift(cursor);
      }
      return path;
    }
    visited.add(key(current));

    const neighbors = [
      { x: current.x, y: current.y - 1 },
      { x: current.x + 1, y: current.y },
      { x: current.x, y: current.y + 1 },
      { x: current.x - 1, y: current.y },
    ];
    for (const neighbor of neighbors) {
      const neighborKey = key(neighbor);
      if (neighbor.x < 0 || neighbor.x >= width || neighbor.y < 0 || neighbor.y >= height) continue;
      if (blocked.has(neighborKey) || visited.has(neighborKey)) continue;
      const newCost = (cost.get(key(current)) ?? 0) + 1;
      if (newCost < (cost.get(neighborKey) ?? Infinity)) {
        cameFrom.set(neighborKey, current);
        cost.set(neighborKey, newCost);
        if (!open.some((candidate) => key(candidate) === neighborKey)) open.push(neighbor);
      }
    }
  }
  return [start];
}

interface Obstacle {
  x: number;
  y: number;
  width: number;
  height: number;
}

const CELL_SIZE = 25;
const GRID_WIDTH = 44;
const GRID_HEIGHT = 28;
const AGENT_PADDING = 8;
const WALLS: Obstacle[] = [
  { x: 151, y: 20, width: 14, height: 145 },
  { x: 151, y: 215, width: 14, height: 45 },
  { x: 151, y: 408, width: 14, height: 252 },
  { x: 790, y: 20, width: 14, height: 145 },
  { x: 790, y: 215, width: 14, height: 18 },
  { x: 804, y: 219, width: 96, height: 14 },
  { x: 950, y: 219, width: 130, height: 14 },
  { x: 813, y: 219, width: 14, height: 121 },
  { x: 813, y: 390, width: 14, height: 86 },
  { x: 158, y: 437, width: 82, height: 14 },
  { x: 310, y: 437, width: 120, height: 14 },
  { x: 500, y: 437, width: 150, height: 14 },
  { x: 720, y: 437, width: 107, height: 14 },
];
const FURNITURE: Obstacle[] = [
  ...Object.entries(POSITIONS)
    .filter(([id]) => id.startsWith("desk-"))
    .map(([, point]) => ({ x: point.x - 54, y: point.y - 108, width: 108, height: 91 })),
  { x: 834, y: 74, width: 204, height: 34 },
  { x: 188, y: 459, width: 145, height: 65 },
  { x: 400, y: 493, width: 158, height: 42 },
  { x: 442, y: 590, width: 73, height: 25 },
  { x: 620, y: 482, width: 155, height: 68 },
  { x: 850, y: 274, width: 190, height: 60 },
  { x: 854, y: 404, width: 182, height: 42 },
  { x: 42, y: 283, width: 88, height: 63 },
];
const OBSTACLES = [...WALLS, ...FURNITURE];

export function isOfficePositionWalkable(point: Point): boolean {
  if (point.x < 24 || point.x > 1076 || point.y < 24 || point.y > 656) return false;
  return !OBSTACLES.some((obstacle) =>
    point.x >= obstacle.x - AGENT_PADDING
    && point.x <= obstacle.x + obstacle.width + AGENT_PADDING
    && point.y >= obstacle.y - AGENT_PADDING
    && point.y <= obstacle.y + obstacle.height + AGENT_PADDING
  );
}

function officeBlocked(start: GridPoint, goal: GridPoint): Set<string> {
  const blocked = new Set<string>();
  for (let y = 0; y < GRID_HEIGHT; y += 1) {
    for (let x = 0; x < GRID_WIDTH; x += 1) {
      const point = { x: (x + 0.5) * CELL_SIZE, y: (y + 0.5) * CELL_SIZE };
      if (!isOfficePositionWalkable(point)) blocked.add(key({ x, y }));
    }
  }
  blocked.delete(key(start));
  blocked.delete(key(goal));
  return blocked;
}

export function routeBetween(start: Point, goal: Point): Point[] {
  const toGrid = (point: Point): GridPoint => ({
    x: Math.max(0, Math.min(GRID_WIDTH - 1, Math.floor(point.x / CELL_SIZE))),
    y: Math.max(0, Math.min(GRID_HEIGHT - 1, Math.floor(point.y / CELL_SIZE))),
  });
  const startCell = toGrid(start);
  const goalCell = toGrid(goal);
  const blocked = officeBlocked(startCell, goalCell);
  const cells = findPath(startCell, goalCell, blocked, GRID_WIDTH, GRID_HEIGHT);
  if (cells.length === 1) return [];
  return [
    ...cells.slice(1, -1).map((cell) => ({
      x: (cell.x + 0.5) * CELL_SIZE,
      y: (cell.y + 0.5) * CELL_SIZE,
    })),
    goal,
  ];
}

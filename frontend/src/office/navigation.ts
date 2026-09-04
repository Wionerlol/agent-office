import type { Point } from "./layout";

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
  return [start, goal];
}

const GRID_WIDTH = 12;
const GRID_HEIGHT = 8;
const CELL_WIDTH = 1100 / GRID_WIDTH;
const CELL_HEIGHT = 680 / GRID_HEIGHT;
const BLOCKED = new Set(["2,2", "4,2", "6,2", "3,4", "6,4"]);

export function routeBetween(start: Point, goal: Point): Point[] {
  const toGrid = (point: Point): GridPoint => ({
    x: Math.max(0, Math.min(GRID_WIDTH - 1, Math.floor(point.x / CELL_WIDTH))),
    y: Math.max(0, Math.min(GRID_HEIGHT - 1, Math.floor(point.y / CELL_HEIGHT))),
  });
  const startCell = toGrid(start);
  const goalCell = toGrid(goal);
  const blocked = new Set(BLOCKED);
  blocked.delete(key(startCell));
  blocked.delete(key(goalCell));
  const cells = findPath(startCell, goalCell, blocked, GRID_WIDTH, GRID_HEIGHT);
  return [
    ...cells.slice(1, -1).map((cell) => ({
      x: (cell.x + 0.5) * CELL_WIDTH,
      y: (cell.y + 0.5) * CELL_HEIGHT,
    })),
    goal,
  ];
}

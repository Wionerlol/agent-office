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

export const OFFICE_WIDTH = 1100;
export const OFFICE_HEIGHT = 680;

export const ZONES: ZoneLayout[] = [
  { id: "entrance", label: "ENTRANCE", x: 28, y: 280, width: 118, height: 110, color: 0xb5cfbf },
  { id: "desk_area", label: "DESK AREA", x: 176, y: 42, width: 610, height: 388, color: 0xd8d0bd },
  { id: "library", label: "LIBRARY", x: 816, y: 42, width: 254, height: 170, color: 0xc5b696 },
  { id: "coffee_area", label: "COFFEE", x: 176, y: 462, width: 182, height: 180, color: 0xb99d7e },
  { id: "lounge", label: "LOUNGE", x: 382, y: 462, width: 192, height: 180, color: 0xc3adba },
  { id: "tool_lab", label: "TOOL LAB", x: 598, y: 462, width: 214, height: 180, color: 0x9eb5b6 },
  { id: "test_lab", label: "TEST LAB", x: 836, y: 246, width: 234, height: 246, color: 0x9baf98 },
  { id: "exit", label: "EXIT", x: 912, y: 536, width: 158, height: 106, color: 0xc49b8c },
];

export const POSITIONS: Record<string, Point> = {
  entrance: { x: 85, y: 340 },
  "desk-1": { x: 275, y: 160 },
  "desk-2": { x: 475, y: 160 },
  "desk-3": { x: 675, y: 160 },
  "desk-4": { x: 355, y: 330 },
  "desk-5": { x: 595, y: 330 },
  library: { x: 942, y: 142 },
  coffee_area: { x: 265, y: 558 },
  lounge: { x: 477, y: 558 },
  tool_lab: { x: 705, y: 558 },
  test_lab: { x: 952, y: 370 },
  exit: { x: 992, y: 588 },
};

export function assignDesk(
  agentId: string,
  assignments: Map<string, string>,
  deskCount = 5,
): string {
  const existing = assignments.get(agentId);
  if (existing) return existing;
  const desks = Array.from({ length: deskCount }, (_, index) => `desk-${index + 1}`);
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

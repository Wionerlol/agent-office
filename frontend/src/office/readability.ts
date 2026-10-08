import type { Point } from "./layout";
import { OFFICE_HEIGHT, OFFICE_WIDTH } from "./layout";

export interface LabelCandidate extends Point {
  id: string; width: number; height: number; priority: number; eligible: boolean;
}
interface LabelBox extends Point { width: number; height: number }
const overlaps = (a: LabelBox, b: LabelBox) => Math.abs(a.x - b.x) < (a.width + b.width) / 2 + 4
  && Math.abs(a.y - b.y) < (a.height + b.height) / 2 + 4;

/** Label positions never feed physical seats/routes. Important plates get first choice. */
export function placeLabels(candidates: readonly LabelCandidate[]): Map<string, Point> {
  const placed: LabelBox[] = [], result = new Map<string, Point>();
  const ordered = [...candidates].sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));
  for (const candidate of ordered) {
    if (!candidate.eligible) continue;
    const x = Math.max(candidate.width / 2 + 4, Math.min(OFFICE_WIDTH - candidate.width / 2 - 4, candidate.x));
    const y = Math.max(candidate.height / 2 + 4, Math.min(OFFICE_HEIGHT - candidate.height / 2 - 4, candidate.y));
    // Important labels can step above/below a crowded row; ordinary labels yield.
    const offsets = candidate.priority >= 2 ? [0, -44, 44, -88, 88, -132, 132] : [0];
    const boxes = offsets.map((dy) => ({ x, y: Math.max(candidate.height / 2 + 4,
      Math.min(OFFICE_HEIGHT - candidate.height / 2 - 4, y + dy)), width: candidate.width, height: candidate.height }));
    const box = boxes.find((b) => !placed.some((p) => overlaps(b, p))) ?? (candidate.priority >= 3 ? boxes[0] : null);
    if (box) { placed.push(box); result.set(candidate.id, { x: box.x, y: box.y }); }
  }
  return result;
}

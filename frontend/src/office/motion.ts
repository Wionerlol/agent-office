import type { VisualState } from "./visual";

export function bodyPose(animation: VisualState, time: number, reduced: boolean) {
  const active = animation === "typing" || animation === "testing" || animation === "working_machine";
  return {
    y: !reduced && active ? Math.sin(time * 2) * 1.5 : 0,
    rotation: !reduced && animation === "celebration" ? Math.sin(time * 2) * 0.12 : 0,
    alpha: !reduced && animation === "error" ? 0.65 + Math.sin(time * 3) * 0.3 : 1,
    attentionAlpha: !reduced && animation === "user_attention" ? 0.85 + Math.sin(time / 3) * 0.15 : 1,
  };
}

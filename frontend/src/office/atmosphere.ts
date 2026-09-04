export type OfficeAtmosphere = "day" | "dusk" | "night";

export function atmosphereForUsage(remainingPercent: number | null): OfficeAtmosphere {
  if (remainingPercent === null || remainingPercent >= 50) return "day";
  if (remainingPercent >= 20) return "dusk";
  return "night";
}

/**
 * Returns an HSL color representing alignment relative to the highest scorer.
 * ratio=0 → red (hue 0), ratio=maxRatio → green (hue 120).
 */
export function getAlignmentColor(ratio: number, maxRatio: number): string {
  const normalized = maxRatio > 0 ? ratio / maxRatio : 0;
  const hue = Math.round(normalized * 120);
  return `hsl(${hue}, 75%, 35%)`;
}

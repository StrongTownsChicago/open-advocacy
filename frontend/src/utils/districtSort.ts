export function compareDistrictNames(
  a: string | null | undefined,
  b: string | null | undefined
): number {
  const aStr = a ?? '';
  const bStr = b ?? '';
  const aNum = parseInt(aStr.match(/\d+/)?.[0] ?? '', 10);
  const bNum = parseInt(bStr.match(/\d+/)?.[0] ?? '', 10);
  if (!isNaN(aNum) && !isNaN(bNum)) return aNum - bNum;
  return aStr.localeCompare(bStr);
}

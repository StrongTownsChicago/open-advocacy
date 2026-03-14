import { Entity, EntityStatus, EntityStatusRecord } from '../../types';
import { compareDistrictNames } from '../../utils/districtSort';

type Order = 'asc' | 'desc';

export const STATUS_SORT_ORDER: Record<string, number> = {
  [EntityStatus.SOLID_APPROVAL]: 0,
  [EntityStatus.LEANING_APPROVAL]: 1,
  [EntityStatus.NEUTRAL]: 2,
  [EntityStatus.LEANING_DISAPPROVAL]: 3,
  [EntityStatus.SOLID_DISAPPROVAL]: 4,
  [EntityStatus.UNKNOWN]: 5,
};

export function compareEntities(
  a: Entity,
  b: Entity,
  orderBy: keyof Entity | 'status' | string,
  order: Order,
  statusRecordsMap: Record<string, EntityStatusRecord>,
  metricKeys: string[]
): number {
  let aVal: unknown;
  let bVal: unknown;

  if (orderBy === 'status') {
    aVal = STATUS_SORT_ORDER[statusRecordsMap[a.id]?.status ?? EntityStatus.UNKNOWN] ?? 5;
    bVal = STATUS_SORT_ORDER[statusRecordsMap[b.id]?.status ?? EntityStatus.UNKNOWN] ?? 5;
  } else if (metricKeys.includes(orderBy)) {
    const aRaw = statusRecordsMap[a.id]?.record_metadata?.[orderBy];
    const bRaw = statusRecordsMap[b.id]?.record_metadata?.[orderBy];
    aVal = aRaw != null ? parseFloat(String(aRaw)) : -Infinity;
    bVal = bRaw != null ? parseFloat(String(bRaw)) : -Infinity;
  } else if (orderBy === 'district_name') {
    const cmp = compareDistrictNames(a.district_name, b.district_name);
    return order === 'asc' ? cmp : -cmp;
  } else {
    aVal = a[orderBy as keyof Entity] ?? '';
    bVal = b[orderBy as keyof Entity] ?? '';
  }

  if ((bVal as number | string) < (aVal as number | string)) return order === 'desc' ? -1 : 1;
  if ((bVal as number | string) > (aVal as number | string)) return order === 'desc' ? 1 : -1;
  return 0;
}

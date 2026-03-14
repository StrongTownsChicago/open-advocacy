import { describe, it, expect } from 'vitest';
import { compareEntities, STATUS_SORT_ORDER } from './entitySort';
import { Entity, EntityStatus, EntityStatusRecord } from '../../types';

const makeEntity = (id: string, name: string, overrides: Partial<Entity> = {}): Entity => ({
  id,
  name,
  entity_type: 'alderman',
  jurisdiction_id: 'jur-1',
  ...overrides,
});

const makeStatusRecord = (
  entityId: string,
  status: EntityStatus,
  metadata: Record<string, unknown> = {}
): EntityStatusRecord => ({
  id: `sr-${entityId}`,
  entity_id: entityId,
  project_id: 'proj-1',
  status,
  record_metadata: metadata,
  updated_at: '2024-01-01T00:00:00Z',
  updated_by: 'admin',
});

describe('STATUS_SORT_ORDER', () => {
  it('assigns lower numbers to more favourable statuses', () => {
    expect(STATUS_SORT_ORDER[EntityStatus.SOLID_APPROVAL]).toBeLessThan(
      STATUS_SORT_ORDER[EntityStatus.LEANING_APPROVAL]
    );
    expect(STATUS_SORT_ORDER[EntityStatus.LEANING_APPROVAL]).toBeLessThan(
      STATUS_SORT_ORDER[EntityStatus.NEUTRAL]
    );
    expect(STATUS_SORT_ORDER[EntityStatus.NEUTRAL]).toBeLessThan(
      STATUS_SORT_ORDER[EntityStatus.LEANING_DISAPPROVAL]
    );
    expect(STATUS_SORT_ORDER[EntityStatus.LEANING_DISAPPROVAL]).toBeLessThan(
      STATUS_SORT_ORDER[EntityStatus.SOLID_DISAPPROVAL]
    );
    expect(STATUS_SORT_ORDER[EntityStatus.SOLID_DISAPPROVAL]).toBeLessThan(
      STATUS_SORT_ORDER[EntityStatus.UNKNOWN]
    );
  });

  it('covers all EntityStatus values', () => {
    for (const status of Object.values(EntityStatus)) {
      expect(STATUS_SORT_ORDER[status]).toBeDefined();
    }
  });
});

describe('compareEntities — entity field sort', () => {
  const a = makeEntity('a', 'Alice');
  const b = makeEntity('b', 'Bob');

  it('sorts by name ascending', () => {
    expect(compareEntities(a, b, 'name', 'asc', {}, [])).toBeLessThan(0);
    expect(compareEntities(b, a, 'name', 'asc', {}, [])).toBeGreaterThan(0);
  });

  it('sorts by name descending (reverses order)', () => {
    expect(compareEntities(a, b, 'name', 'desc', {}, [])).toBeGreaterThan(0);
    expect(compareEntities(b, a, 'name', 'desc', {}, [])).toBeLessThan(0);
  });

  it('returns 0 for equal names', () => {
    const twin = makeEntity('c', 'Alice');
    expect(compareEntities(a, twin, 'name', 'asc', {}, [])).toBe(0);
  });

  it('treats missing optional fields as empty string (sorts first ascending)', () => {
    const withTitle = makeEntity('x', 'X', { title: 'Alderperson' });
    const noTitle = makeEntity('y', 'Y');
    // empty string < 'Alderperson', so noTitle sorts first
    expect(compareEntities(noTitle, withTitle, 'title', 'asc', {}, [])).toBeLessThan(0);
  });
});

describe('compareEntities — status sort', () => {
  const entityA = makeEntity('a', 'Alice');
  const entityB = makeEntity('b', 'Bob');

  const recordMap: Record<string, EntityStatusRecord> = {
    a: makeStatusRecord('a', EntityStatus.SOLID_APPROVAL),
    b: makeStatusRecord('b', EntityStatus.SOLID_DISAPPROVAL),
  };

  it('sorts approval before disapproval ascending', () => {
    expect(compareEntities(entityA, entityB, 'status', 'asc', recordMap, [])).toBeLessThan(0);
  });

  it('sorts disapproval before approval descending', () => {
    expect(compareEntities(entityA, entityB, 'status', 'desc', recordMap, [])).toBeGreaterThan(0);
  });

  it('treats missing status record as UNKNOWN (sorts last ascending)', () => {
    const entityC = makeEntity('c', 'Carol'); // no record
    const entityD = makeEntity('d', 'Dave');
    const sparseMap: Record<string, EntityStatusRecord> = {
      d: makeStatusRecord('d', EntityStatus.NEUTRAL),
    };
    // UNKNOWN (5) > NEUTRAL (2), so c sorts after d
    expect(compareEntities(entityC, entityD, 'status', 'asc', sparseMap, [])).toBeGreaterThan(0);
  });

  it('returns 0 for equal statuses', () => {
    const sameMap: Record<string, EntityStatusRecord> = {
      a: makeStatusRecord('a', EntityStatus.NEUTRAL),
      b: makeStatusRecord('b', EntityStatus.NEUTRAL),
    };
    expect(compareEntities(entityA, entityB, 'status', 'asc', sameMap, [])).toBe(0);
  });

  it('sorts all statuses in correct precedence order ascending', () => {
    const statuses = [
      EntityStatus.UNKNOWN,
      EntityStatus.SOLID_DISAPPROVAL,
      EntityStatus.LEANING_DISAPPROVAL,
      EntityStatus.NEUTRAL,
      EntityStatus.LEANING_APPROVAL,
      EntityStatus.SOLID_APPROVAL,
    ];
    const entities = statuses.map((_s, i) => makeEntity(String(i), String(i)));
    const map: Record<string, EntityStatusRecord> = {};
    statuses.forEach((status, i) => {
      map[String(i)] = makeStatusRecord(String(i), status);
    });

    const sorted = [...entities].sort((a, b) => compareEntities(a, b, 'status', 'asc', map, []));
    const sortedStatuses = sorted.map(e => map[e.id].status);
    expect(sortedStatuses).toEqual([
      EntityStatus.SOLID_APPROVAL,
      EntityStatus.LEANING_APPROVAL,
      EntityStatus.NEUTRAL,
      EntityStatus.LEANING_DISAPPROVAL,
      EntityStatus.SOLID_DISAPPROVAL,
      EntityStatus.UNKNOWN,
    ]);
  });
});

describe('compareEntities — district_name sort', () => {
  it('sorts Ward 2 before Ward 10 ascending (numeric)', () => {
    const ward2 = makeEntity('a', 'Alice', { district_name: 'Ward 2' });
    const ward10 = makeEntity('b', 'Bob', { district_name: 'Ward 10' });
    expect(compareEntities(ward2, ward10, 'district_name', 'asc', {}, [])).toBeLessThan(0);
  });

  it('sorts Ward 10 before Ward 2 descending', () => {
    const ward2 = makeEntity('a', 'Alice', { district_name: 'Ward 2' });
    const ward10 = makeEntity('b', 'Bob', { district_name: 'Ward 10' });
    expect(compareEntities(ward2, ward10, 'district_name', 'desc', {}, [])).toBeGreaterThan(0);
  });

  it('treats null district_name as empty string (sorts first ascending)', () => {
    const noDistrict = makeEntity('a', 'Alice', { district_name: undefined });
    const ward5 = makeEntity('b', 'Bob', { district_name: 'Ward 5' });
    // empty string < 'Ward 5' via localeCompare (no number in '')
    expect(compareEntities(noDistrict, ward5, 'district_name', 'asc', {}, [])).toBeLessThan(0);
  });

  it('returns 0 for equal district names', () => {
    const a = makeEntity('a', 'Alice', { district_name: 'Ward 7' });
    const b = makeEntity('b', 'Bob', { district_name: 'Ward 7' });
    expect(compareEntities(a, b, 'district_name', 'asc', {}, [])).toBe(0);
  });
});

describe('compareEntities — metric sort', () => {
  const entityA = makeEntity('a', 'Alice');
  const entityB = makeEntity('b', 'Bob');
  const metricKeys = ['rs_zoned_pct'];

  const recordMap: Record<string, EntityStatusRecord> = {
    a: makeStatusRecord('a', EntityStatus.UNKNOWN, { rs_zoned_pct: 82.5 }),
    b: makeStatusRecord('b', EntityStatus.UNKNOWN, { rs_zoned_pct: 45.0 }),
  };

  it('sorts higher metric value first ascending', () => {
    // 82.5 > 45.0, so a (82.5) should come after b (45.0) ascending
    expect(compareEntities(entityA, entityB, 'rs_zoned_pct', 'asc', recordMap, metricKeys)).toBeGreaterThan(0);
  });

  it('sorts higher metric value first descending', () => {
    expect(compareEntities(entityA, entityB, 'rs_zoned_pct', 'desc', recordMap, metricKeys)).toBeLessThan(0);
  });

  it('treats null metadata value as -Infinity (sorts last ascending)', () => {
    const entityC = makeEntity('c', 'Carol');
    const sparseMap: Record<string, EntityStatusRecord> = {
      a: makeStatusRecord('a', EntityStatus.UNKNOWN, { rs_zoned_pct: 10 }),
      c: makeStatusRecord('c', EntityStatus.UNKNOWN, {}), // no rs_zoned_pct
    };
    // null → -Infinity, so c sorts before a ascending? No: -Infinity < 10, so c comes first ascending
    expect(compareEntities(entityA, entityC, 'rs_zoned_pct', 'asc', sparseMap, metricKeys)).toBeGreaterThan(0);
  });

  it('treats missing status record as -Infinity for metric (sorts last ascending)', () => {
    const entityC = makeEntity('c', 'Carol'); // no record at all
    const sparseMap: Record<string, EntityStatusRecord> = {
      a: makeStatusRecord('a', EntityStatus.UNKNOWN, { rs_zoned_pct: 10 }),
    };
    expect(compareEntities(entityA, entityC, 'rs_zoned_pct', 'asc', sparseMap, metricKeys)).toBeGreaterThan(0);
  });

  it('returns 0 for equal metric values', () => {
    const tiedMap: Record<string, EntityStatusRecord> = {
      a: makeStatusRecord('a', EntityStatus.UNKNOWN, { rs_zoned_pct: 50 }),
      b: makeStatusRecord('b', EntityStatus.UNKNOWN, { rs_zoned_pct: 50 }),
    };
    expect(compareEntities(entityA, entityB, 'rs_zoned_pct', 'asc', tiedMap, metricKeys)).toBe(0);
  });

  it('falls back to entity field sort when key is not in metricKeys', () => {
    // 'rs_zoned_pct' not in metricKeys → treated as entity field, both entities have no such field → 0
    expect(compareEntities(entityA, entityB, 'rs_zoned_pct', 'asc', recordMap, [])).toBe(0);
  });

  it('parses string metric values as floats', () => {
    const stringMap: Record<string, EntityStatusRecord> = {
      a: makeStatusRecord('a', EntityStatus.UNKNOWN, { rs_zoned_pct: '75.3' }),
      b: makeStatusRecord('b', EntityStatus.UNKNOWN, { rs_zoned_pct: '20.1' }),
    };
    // ascending: b (20.1) before a (75.3)
    expect(compareEntities(entityA, entityB, 'rs_zoned_pct', 'asc', stringMap, metricKeys)).toBeGreaterThan(0);
  });
});

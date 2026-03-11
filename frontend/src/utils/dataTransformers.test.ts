import { describe, it, expect } from 'vitest';
import {
  transformProjectFromApi,
  transformEntityFromApi,
  transformGroupFromApi,
} from './dataTransformers';
import { EntityStatus, ProjectStatus } from '../types';

describe('transformProjectFromApi', () => {
  it('maps all fields correctly from a complete API response', () => {
    const apiProject = {
      id: 'proj-1',
      title: 'Test Project',
      description: 'A description',
      status: 'active',
      active: true,
      link: 'https://example.com',
      preferred_status: 'solid_approval',
      template_response: 'Template text',
      jurisdiction_id: 'jur-1',
      jurisdiction_name: 'Chicago',
      group_id: 'grp-1',
      created_by: 'admin',
      created_at: '2024-01-01',
      updated_at: '2024-01-02',
      status_distribution: {
        solid_approval: 5,
        leaning_approval: 3,
        neutral: 2,
        leaning_disapproval: 1,
        solid_disapproval: 0,
        unknown: 10,
        total: 21,
      },
    };

    const result = transformProjectFromApi(apiProject);
    expect(result.id).toBe('proj-1');
    expect(result.title).toBe('Test Project');
    expect(result.status).toBe(ProjectStatus.ACTIVE);
    expect(result.preferred_status).toBe(EntityStatus.SOLID_APPROVAL);
    expect(result.status_distribution!.total).toBe(21);
  });

  it('provides default values for missing optional fields', () => {
    const apiProject = {
      id: 'proj-2',
      title: 'Minimal',
      status: 'draft',
      active: true,
      jurisdiction_id: 'jur-1',
      group_id: 'grp-1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    };

    const result = transformProjectFromApi(apiProject);
    expect(result.description).toBe('');
    expect(result.link).toBe('');
    expect(result.template_response).toBe('');
    expect(result.created_by).toBe('');
    expect(result.preferred_status).toBe(EntityStatus.SOLID_APPROVAL);
  });

  it('provides default StatusDistribution when missing', () => {
    const apiProject = {
      id: 'proj-3',
      title: 'No Distribution',
      status: 'active',
      active: true,
      jurisdiction_id: 'jur-1',
      group_id: 'grp-1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    };

    const result = transformProjectFromApi(apiProject);
    expect(result.status_distribution).toEqual({
      solid_approval: 0,
      leaning_approval: 0,
      neutral: 0,
      leaning_disapproval: 0,
      solid_disapproval: 0,
      unknown: 0,
      total: 0,
    });
  });
});

describe('transformEntityFromApi', () => {
  it('maps all fields correctly from a complete API response', () => {
    const apiEntity = {
      id: 'ent-1',
      name: 'Jane Doe',
      title: 'Alderperson',
      entity_type: 'alderman',
      email: 'jane@example.com',
      phone: '555-1234',
      website: 'https://jane.example.com',
      address: '123 Main St',
      district_name: 'Ward 1',
      jurisdiction_id: 'jur-1',
      image_url: 'https://example.com/jane.jpg',
    };

    const result = transformEntityFromApi(apiEntity);
    expect(result.id).toBe('ent-1');
    expect(result.name).toBe('Jane Doe');
    expect(result.title).toBe('Alderperson');
    expect(result.email).toBe('jane@example.com');
    expect(result.image_url).toBe('https://example.com/jane.jpg');
  });

  it('provides default empty strings for missing optional fields', () => {
    const apiEntity = {
      id: 'ent-2',
      name: 'Minimal Entity',
      entity_type: 'state_rep',
      jurisdiction_id: 'jur-1',
    };

    const result = transformEntityFromApi(apiEntity);
    expect(result.title).toBe('');
    expect(result.email).toBe('');
    expect(result.phone).toBe('');
    expect(result.website).toBe('');
    expect(result.address).toBe('');
    expect(result.district_name).toBe('');
    expect(result.image_url).toBe('');
  });
});

describe('transformGroupFromApi', () => {
  it('maps all fields correctly', () => {
    const apiGroup = {
      id: 'grp-1',
      name: 'Test Group',
      description: 'A group',
      created_at: '2024-01-01',
    };

    const result = transformGroupFromApi(apiGroup);
    expect(result.id).toBe('grp-1');
    expect(result.name).toBe('Test Group');
    expect(result.description).toBe('A group');
    expect(result.created_at).toBe('2024-01-01');
  });

  it('provides default empty string for missing description', () => {
    const apiGroup = {
      id: 'grp-2',
      name: 'Minimal',
      created_at: '2024-01-01',
    };

    const result = transformGroupFromApi(apiGroup);
    expect(result.description).toBe('');
  });
});

describe('transformProjectFromApi — edge cases', () => {
  it('handles null status_distribution', () => {
    const apiProject = {
      id: 'proj-null',
      title: 'Null Distribution',
      status: 'active',
      active: true,
      jurisdiction_id: 'jur-1',
      group_id: 'grp-1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      status_distribution: null,
    };

    const result = transformProjectFromApi(apiProject);
    expect(result.status_distribution).toEqual({
      solid_approval: 0,
      leaning_approval: 0,
      neutral: 0,
      leaning_disapproval: 0,
      solid_disapproval: 0,
      unknown: 0,
      total: 0,
    });
  });

  it('preserves jurisdiction_name when present', () => {
    const apiProject = {
      id: 'proj-jur',
      title: 'With Jurisdiction',
      status: 'active',
      active: true,
      jurisdiction_id: 'jur-1',
      jurisdiction_name: 'City of Chicago',
      group_id: 'grp-1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    };

    const result = transformProjectFromApi(apiProject);
    expect(result.jurisdiction_name).toBe('City of Chicago');
  });
});

describe('transformEntityFromApi — edge cases', () => {
  it('handles entity with all null optional fields', () => {
    const apiEntity = {
      id: 'ent-null',
      name: 'Null Fields Entity',
      entity_type: 'alderman',
      jurisdiction_id: 'jur-1',
      title: null,
      email: null,
      phone: null,
      website: null,
      address: null,
      district_name: null,
      image_url: null,
    };

    const result = transformEntityFromApi(apiEntity);
    expect(result.title).toBe('');
    expect(result.email).toBe('');
    expect(result.phone).toBe('');
    expect(result.website).toBe('');
    expect(result.address).toBe('');
    expect(result.district_name).toBe('');
    expect(result.image_url).toBe('');
  });
});

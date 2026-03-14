import { EntityStatus } from '../types';

export const getStatusColor = (status: EntityStatus): string => {
  switch (status) {
    case EntityStatus.SOLID_APPROVAL:
      return '#166534'; // Deep green — committed action
    case EntityStatus.LEANING_APPROVAL:
      return '#22c55e'; // Bright medium green — clearly positive but incomplete, high contrast vs deep green
    case EntityStatus.NEUTRAL:
      return '#64748b'; // Cool blue-gray — outside the system, not applicable
    case EntityStatus.LEANING_DISAPPROVAL:
      return '#f97316'; // Orange — action needed, persuadable
    case EntityStatus.SOLID_DISAPPROVAL:
      return '#dc2626'; // Red — active opposition
    default:
      return '#94a3b8'; // Light blue-gray — no data, clearly distinct from neutral
  }
};

export const getStatusLabel = (status: EntityStatus): string => {
  switch (status) {
    case EntityStatus.SOLID_APPROVAL:
      return 'Solid Approval';
    case EntityStatus.LEANING_APPROVAL:
      return 'Leaning Approval';
    case EntityStatus.NEUTRAL:
      return 'Neutral';
    case EntityStatus.LEANING_DISAPPROVAL:
      return 'Leaning Disapproval';
    case EntityStatus.SOLID_DISAPPROVAL:
      return 'Solid Disapproval';
    default:
      return 'Unknown';
  }
};

export const makeStatusLabelFn = (
  statusLabels?: Record<string, string>
) => (status: EntityStatus): string => {
  if (statusLabels?.[status]) return statusLabels[status];
  return getStatusLabel(status);
};

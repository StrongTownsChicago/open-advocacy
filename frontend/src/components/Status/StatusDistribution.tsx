import React from 'react';
import { Box, Typography, Tooltip } from '@mui/material';
import { StatusDistribution as StatusDistributionType, EntityStatus } from '../../types';
import { getStatusColor, makeStatusLabelFn } from '../../utils/statusColors';

interface StatusBarProps {
  distribution: StatusDistributionType;
  size?: 'small' | 'medium' | 'large';
  showLabels?: boolean;
  showPercentages?: boolean;
  showCounts?: boolean;
  statusLabels?: Record<string, string>;
}

const StatusDistribution: React.FC<StatusBarProps> = ({
  distribution,
  size = 'medium',
  showLabels = false,
  showPercentages = false,
  showCounts = false,
  statusLabels,
}) => {
  const getStatusLabel = makeStatusLabelFn(statusLabels);
  const total = distribution.total || 1;
  const barHeight = size === 'small' ? 8 : size === 'medium' ? 16 : 24;
  const fontSize = size === 'small' ? 10 : size === 'medium' ? 12 : 14;

  const sections = [
    { status: EntityStatus.SOLID_APPROVAL, count: distribution.solid_approval },
    { status: EntityStatus.LEANING_APPROVAL, count: distribution.leaning_approval },
    { status: EntityStatus.NEUTRAL, count: distribution.neutral },
    { status: EntityStatus.LEANING_DISAPPROVAL, count: distribution.leaning_disapproval },
    { status: EntityStatus.SOLID_DISAPPROVAL, count: distribution.solid_disapproval },
    { status: EntityStatus.UNKNOWN, count: distribution.unknown },
  ];

  return (
    <Box>
      {showLabels && (
        <Typography variant="subtitle2" gutterBottom>
          Status Distribution
        </Typography>
      )}

      <Box
        sx={{
          display: 'flex',
          width: '100%',
          height: barHeight,
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        {sections.map((section, index) => {
          if (section.count === 0) return null;
          const percentage = (section.count / total) * 100;
          return (
            <Tooltip
              key={index}
              title={`${getStatusLabel(section.status)}: ${section.count} (${percentage.toFixed(1)}%)`}
            >
              <Box
                sx={{
                  width: `${percentage}%`,
                  height: '100%',
                  backgroundColor: getStatusColor(section.status),
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  color: '#fff',
                  fontSize: fontSize,
                  fontWeight: 'bold',
                  minWidth: percentage < 8 ? 'auto' : 20,
                }}
              >
                {showPercentages && percentage >= 8 && `${Math.round(percentage)}%`}
              </Box>
            </Tooltip>
          );
        })}
      </Box>

      {distribution.total === 0 && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          No status data available
        </Typography>
      )}

      {showCounts && distribution.total > 0 && (
        <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {sections.map((section, index) => {
            if (section.count === 0) return null;
            return (
              <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '2px',
                    bgcolor: getStatusColor(section.status),
                  }}
                />
                <Typography variant="body2" component="span">
                  {getStatusLabel(section.status)}: {section.count}
                </Typography>
              </Box>
            );
          })}
          <Typography variant="body2" component="span" fontWeight="bold">
            Total: {distribution.total}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default StatusDistribution;

import React from 'react';
import { Box, Typography, Tooltip, useTheme } from '@mui/material';
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
  const theme = useTheme();
  const getStatusLabel = makeStatusLabelFn(statusLabels);
  const total = distribution.total || 1;
  const barHeight = size === 'small' ? 8 : size === 'medium' ? 12 : 18;
  const fontSize = size === 'small' ? 10 : size === 'medium' ? 11 : 13;

  const sections = [
    { status: EntityStatus.SOLID_APPROVAL, count: distribution.solid_approval },
    { status: EntityStatus.LEANING_APPROVAL, count: distribution.leaning_approval },
    { status: EntityStatus.NEUTRAL, count: distribution.neutral },
    { status: EntityStatus.LEANING_DISAPPROVAL, count: distribution.leaning_disapproval },
    { status: EntityStatus.SOLID_DISAPPROVAL, count: distribution.solid_disapproval },
    { status: EntityStatus.UNKNOWN, count: distribution.unknown },
  ].filter(s => s.count > 0);

  const isLight = theme.palette.mode === 'light';

  if (size === 'large' && showCounts && distribution.total > 0) {
    return (
      <Box>
        {showLabels && (
          <Typography
            variant="subtitle2"
            sx={{ mb: 2, color: 'text.secondary', letterSpacing: '0.08em' }}
          >
            Status Distribution
          </Typography>
        )}

        {/* Stat cards row */}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1.5,
            mb: 2,
          }}
        >
          {sections.map((section, index) => {
            const percentage = (section.count / distribution.total) * 100;
            const color = getStatusColor(section.status);
            return (
              <Box
                key={index}
                sx={{
                  flex: '1 1 120px',
                  minWidth: 100,
                  px: 2,
                  py: 1.5,
                  borderRadius: 2,
                  backgroundColor: isLight
                    ? `${color}12`
                    : `${color}20`,
                  border: `1px solid ${color}30`,
                  borderLeft: `3px solid ${color}`,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    backgroundColor: isLight ? `${color}20` : `${color}30`,
                    transform: 'translateY(-1px)',
                  },
                }}
              >
                <Typography
                  sx={{
                    fontSize: '1.5rem',
                    fontWeight: 700,
                    fontFamily: '"Fraunces", Georgia, serif',
                    color: color,
                    lineHeight: 1.1,
                  }}
                >
                  {section.count}
                </Typography>
                <Typography
                  sx={{
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    color: 'text.secondary',
                    mt: 0.25,
                    lineHeight: 1.3,
                  }}
                >
                  {getStatusLabel(section.status)}
                </Typography>
                <Typography
                  sx={{
                    fontSize: '0.68rem',
                    color: color,
                    fontWeight: 600,
                    opacity: 0.85,
                    mt: 0.25,
                  }}
                >
                  {percentage.toFixed(0)}%
                </Typography>
              </Box>
            );
          })}

          {/* Total card */}
          <Box
            sx={{
              flex: '1 1 120px',
              minWidth: 100,
              px: 2,
              py: 1.5,
              borderRadius: 2,
              backgroundColor: isLight ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.08)'}`,
              borderLeft: `3px solid ${isLight ? 'rgba(0,0,0,0.15)' : 'rgba(255,255,255,0.15)'}`,
            }}
          >
            <Typography
              sx={{
                fontSize: '1.5rem',
                fontWeight: 700,
                fontFamily: '"Fraunces", Georgia, serif',
                color: 'text.primary',
                lineHeight: 1.1,
              }}
            >
              {distribution.total}
            </Typography>
            <Typography
              sx={{
                fontSize: '0.72rem',
                fontWeight: 600,
                color: 'text.secondary',
                mt: 0.25,
                lineHeight: 1.3,
              }}
            >
              Total
            </Typography>
          </Box>
        </Box>

        {/* Progress bar */}
        <Box
          sx={{
            display: 'flex',
            width: '100%',
            height: barHeight,
            borderRadius: 1.5,
            overflow: 'hidden',
            boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.1)',
          }}
        >
          {sections.map((section, index) => {
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
                    minWidth: percentage < 6 ? 'auto' : 20,
                    transition: 'width 0.3s ease',
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
      </Box>
    );
  }

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
          borderRadius: 1.5,
          overflow: 'hidden',
          boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.08)',
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
        <Box sx={{ mt: 1.5, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {sections.map((section, index) => {
            if (section.count === 0) return null;
            return (
              <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '3px',
                    bgcolor: getStatusColor(section.status),
                    flexShrink: 0,
                  }}
                />
                <Typography variant="body2" component="span" sx={{ fontSize: '0.8rem' }}>
                  {getStatusLabel(section.status)}:{' '}
                  <strong>{section.count}</strong>
                </Typography>
              </Box>
            );
          })}
          <Typography variant="body2" component="span" fontWeight="bold" sx={{ fontSize: '0.8rem' }}>
            Total: {distribution.total}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default StatusDistribution;

import React from 'react';
import { Box, LinearProgress, Tooltip, Typography } from '@mui/material';
import { getScoreColor } from './scoreColor';

interface ScoreCellProps {
  scoreCount: number;
  totalScoreable: number;
  maxRatio: number;
}

const ScoreCell: React.FC<ScoreCellProps> = ({ scoreCount, totalScoreable, maxRatio }) => {
  const ratio = totalScoreable > 0 ? scoreCount / totalScoreable : 0;
  const pct = Math.round(ratio * 100);
  const color = getScoreColor(ratio, maxRatio);

  return (
    <Tooltip title={`${pct}% score (${scoreCount} of ${totalScoreable} issues)`} arrow>
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5, minWidth: 72 }}>
        <Typography variant="body2" fontWeight={700} sx={{ color, lineHeight: 1 }}>
          {scoreCount} / {totalScoreable}
        </Typography>
        <LinearProgress
          variant="determinate"
          value={pct}
          sx={{
            width: '100%',
            height: 4,
            borderRadius: 2,
            backgroundColor: '#e0e0e0',
            '& .MuiLinearProgress-bar': { backgroundColor: color, borderRadius: 2 },
          }}
        />
      </Box>
    </Tooltip>
  );
};

export default ScoreCell;

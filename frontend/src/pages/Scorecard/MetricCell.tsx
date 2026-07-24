import React from 'react';
import { TableCell, Typography } from '@mui/material';
import { formatMetricValue } from './metricFormat';

interface MetricCellProps {
  value: number | string | null | undefined;
  format?: string;
}

const MetricCell: React.FC<MetricCellProps> = ({ value, format }) => (
  <TableCell align="right">
    <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
      {formatMetricValue(value, format)}
    </Typography>
  </TableCell>
);

export default MetricCell;

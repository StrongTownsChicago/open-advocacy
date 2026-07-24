import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Table, TableBody, TableRow } from '@mui/material';
import MetricCell from './MetricCell';
import { EMPTY_METRIC_LABEL } from './metricFormat';

describe('MetricCell', () => {
  function renderCell(value: number | string | null | undefined, format?: string) {
    return render(
      <Table>
        <TableBody>
          <TableRow>
            <MetricCell value={value} format={format} />
          </TableRow>
        </TableBody>
      </Table>
    );
  }

  it('renders the formatted value', () => {
    renderCell(128);
    expect(screen.getByText('128')).toBeInTheDocument();
  });

  it('renders an em dash for a missing value', () => {
    renderCell(null);
    expect(screen.getByText(EMPTY_METRIC_LABEL)).toBeInTheDocument();
  });

  it('is right-aligned', () => {
    renderCell(3);
    expect(screen.getByRole('cell')).toHaveStyle({ textAlign: 'right' });
  });
});

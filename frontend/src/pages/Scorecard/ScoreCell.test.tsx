import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ScoreCell from './ScoreCell';
import { getScoreColor } from './scoreColor';

describe('getScoreColor', () => {
  it('top scorer (ratio === maxRatio) gets green', () => {
    expect(getScoreColor(1, 1)).toBe('hsl(120, 75%, 35%)');
    expect(getScoreColor(0.6, 0.6)).toBe('hsl(120, 75%, 35%)');
  });

  it('zero ratio gets red regardless of maxRatio', () => {
    expect(getScoreColor(0, 1)).toBe('hsl(0, 75%, 35%)');
    expect(getScoreColor(0, 0.8)).toBe('hsl(0, 75%, 35%)');
  });

  it('midpoint relative to max gets yellow (hue ~60)', () => {
    expect(getScoreColor(0.5, 1)).toBe('hsl(60, 75%, 35%)');
  });

  it('color scales continuously — lower ratio produces lower hue than higher ratio', () => {
    const low = getScoreColor(0.2, 1);
    const mid = getScoreColor(0.5, 1);
    const high = getScoreColor(0.8, 1);
    const hue = (s: string) => parseInt(s.match(/hsl\((\d+)/)![1]);
    expect(hue(low)).toBeLessThan(hue(mid));
    expect(hue(mid)).toBeLessThan(hue(high));
  });

  it('handles zero maxRatio without crashing', () => {
    expect(() => getScoreColor(0, 0)).not.toThrow();
    expect(getScoreColor(0, 0)).toBe('hsl(0, 75%, 35%)');
  });
});

describe('ScoreCell', () => {
  function renderScoreCell(scoreCount: number, totalScoreable: number, maxRatio = 1) {
    return render(
      <MemoryRouter>
        <ScoreCell scoreCount={scoreCount} totalScoreable={totalScoreable} maxRatio={maxRatio} />
      </MemoryRouter>
    );
  }

  it('renders the fraction label', () => {
    renderScoreCell(8, 12);
    expect(screen.getByText('8 / 12')).toBeInTheDocument();
  });

  it('renders zero-denominator safely without crashing', () => {
    renderScoreCell(0, 0);
    expect(screen.getByText('0 / 0')).toBeInTheDocument();
  });

  it('renders a progress bar', () => {
    renderScoreCell(6, 12);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
});

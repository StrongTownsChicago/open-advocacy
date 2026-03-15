import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../theme/ThemeProvider';

// Mock the api module before importing the component
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

import ScorecardIndex from './ScorecardIndex';
import api from '../services/api';

const mockGroups = [
  { id: '1', name: 'Strong Towns Chicago' },
  { id: '2', name: 'Abundant Housing Illinois' },
  { id: '3', name: 'Abundant Housing Illinois — IL House' },
  { id: '4', name: 'Abundant Housing Illinois — IL Senate' },
];

function renderScorecardIndex() {
  return render(
    <MemoryRouter initialEntries={['/scorecard']}>
      <ThemeProvider>
        <ScorecardIndex />
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('ScorecardIndex', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner before groups API resolves', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}));
    renderScorecardIndex();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders group names as links after successful fetch', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: mockGroups });
    renderScorecardIndex();
    expect(await screen.findByText('Strong Towns Chicago')).toBeInTheDocument();
    expect(screen.getByText('Abundant Housing Illinois')).toBeInTheDocument();
    expect(screen.getByText('Abundant Housing Illinois — IL House')).toBeInTheDocument();
    expect(screen.getByText('Abundant Housing Illinois — IL Senate')).toBeInTheDocument();
  });

  it('group links use correct slugs for ASCII names', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [{ id: '1', name: 'Strong Towns Chicago' }],
    });
    renderScorecardIndex();
    const link = await screen.findByRole('link', { name: 'Strong Towns Chicago' });
    expect(link).toHaveAttribute('href', '/scorecard/strong-towns-chicago');
  });

  it('group link uses correct slug with em dash in name', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: [{ id: '3', name: 'Abundant Housing Illinois — IL House' }],
    });
    renderScorecardIndex();
    const link = await screen.findByRole('link', {
      name: 'Abundant Housing Illinois — IL House',
    });
    expect(link).toHaveAttribute('href', '/scorecard/abundant-housing-illinois-il-house');
  });

  it('renders error state when groups API call fails', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('Network error'));
    renderScorecardIndex();
    const errorText = await screen.findByText(/failed to load scorecard groups/i);
    expect(errorText).toBeInTheDocument();
  });

  it('renders empty state message when groups array is empty', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    renderScorecardIndex();
    expect(
      await screen.findByText(/no scorecard groups available/i)
    ).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});

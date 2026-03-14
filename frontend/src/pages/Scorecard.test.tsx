import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ThemeProvider } from '../theme/ThemeProvider';
import { EntityStatus, ScorecardResponse } from '../types';

// Mock the scorecard service before importing the component
vi.mock('../services/scorecard', () => ({
  scorecardService: {
    getScorecard: vi.fn(),
  },
}));

import Scorecard from './Scorecard';
import { scorecardService } from '../services/scorecard';

const mockScorecardResponse: ScorecardResponse = {
  projects: [
    {
      id: 'project-1',
      title: 'ADU Citywide Vote',
      slug: 'adu-citywide-vote',
      preferred_status: EntityStatus.SOLID_APPROVAL,
      status_labels: {
        solid_approval: 'Voted Yes',
        solid_disapproval: 'Voted No',
        unknown: 'Absent',
      },
    },
    {
      id: 'project-2',
      title: 'No Parking Minimums Vote',
      slug: 'no-parking-vote',
      preferred_status: EntityStatus.SOLID_APPROVAL,
      status_labels: {
        solid_approval: 'Voted Yes',
        unknown: 'Absent',
      },
    },
  ],
  entities: [
    {
      entity: {
        id: 'entity-1',
        name: 'Maria Hadden',
        entity_type: 'alderperson',
        district_name: 'Ward 49',
        jurisdiction_id: 'jur-1',
      },
      statuses: {
        'project-1': { status: EntityStatus.SOLID_APPROVAL, label: 'Voted Yes' },
        'project-2': { status: EntityStatus.UNKNOWN, label: 'Absent' },
      },
      aligned_count: 1,
      total_scoreable: 2,
    },
    {
      entity: {
        id: 'entity-2',
        name: 'Carlos Ramirez-Rosa',
        entity_type: 'alderperson',
        district_name: 'Ward 35',
        jurisdiction_id: 'jur-1',
      },
      statuses: {
        'project-1': { status: EntityStatus.SOLID_APPROVAL, label: 'Voted Yes' },
        'project-2': { status: EntityStatus.SOLID_APPROVAL, label: 'Voted Yes' },
      },
      aligned_count: 2,
      total_scoreable: 2,
    },
  ],
};

function renderScorecard(groupSlug = 'strong-towns-chicago') {
  return render(
    <MemoryRouter initialEntries={[`/scorecard/${groupSlug}`]}>
      <ThemeProvider>
        <Routes>
          <Route path="/scorecard/:groupSlug" element={<Scorecard />} />
        </Routes>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Scorecard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading spinner before data arrives', () => {
    // Never resolves
    vi.mocked(scorecardService.getScorecard).mockReturnValue(new Promise(() => {}));
    renderScorecard();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders error state when API call fails', async () => {
    vi.mocked(scorecardService.getScorecard).mockRejectedValue(new Error('Network error'));
    renderScorecard();
    const errorText = await screen.findByText(/failed to load scorecard data/i);
    expect(errorText).toBeInTheDocument();
  });

  it('renders table headers for each project', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: mockScorecardResponse,
    } as never);
    renderScorecard();
    // Project titles appear in column headers (may be abbreviated)
    expect(await screen.findByText(/ADU Citywide Vote/i)).toBeInTheDocument();
  });

  it('renders entity name in table row', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: mockScorecardResponse,
    } as never);
    renderScorecard();
    expect(await screen.findByText('Maria Hadden')).toBeInTheDocument();
  });

  it('renders alignment score as "X / Y" format', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: mockScorecardResponse,
    } as never);
    renderScorecard();
    // Maria Hadden has 1/2, Carlos has 2/2
    expect(await screen.findByText('1 / 2')).toBeInTheDocument();
    expect(screen.getByText('2 / 2')).toBeInTheDocument();
  });

  it('entity name links to representative detail page', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: mockScorecardResponse,
    } as never);
    renderScorecard();
    const link = await screen.findByRole('link', { name: 'Maria Hadden' });
    expect(link).toHaveAttribute('href', '/representatives/entity-1');
  });

  it('renders empty state when no entities returned', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: { projects: [], entities: [] },
    } as never);
    renderScorecard();
    expect(await screen.findByText(/no scorecard data available/i)).toBeInTheDocument();
  });

  it('sort by alignment score re-orders rows', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: mockScorecardResponse,
    } as never);
    renderScorecard();

    // Wait for table to render
    await screen.findByText('Maria Hadden');

    // Carlos has score 2/2, Maria has 1/2, so Carlos should be first by default (desc)
    const rows = screen.getAllByRole('row');
    const firstDataRow = rows[1]; // rows[0] is the header
    expect(firstDataRow).toHaveTextContent('Carlos Ramirez-Rosa');

    // Click the Score sort label to toggle to ascending
    const scoreSortLabel = screen.getByText('Score');
    fireEvent.click(scoreSortLabel);

    const rowsAfterSort = screen.getAllByRole('row');
    const firstDataRowAfterSort = rowsAfterSort[1];
    expect(firstDataRowAfterSort).toHaveTextContent('Maria Hadden');
  });
});

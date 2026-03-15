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

import Scorecard from './Scorecard/index';
import { scorecardService } from '../services/scorecard';

const mockScorecardResponse: ScorecardResponse = {
  group_name: 'Test Group',
  representative_title: 'Alderperson',
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

// Extended mock data with wards 2, 9, 10 and varied project statuses
const extendedScorecardResponse: ScorecardResponse = {
  group_name: 'Test Group',
  representative_title: 'Alderperson',
  projects: [
    {
      id: 'project-1',
      title: 'ADU Citywide Vote',
      slug: 'adu-citywide-vote',
      preferred_status: EntityStatus.SOLID_APPROVAL,
      status_labels: { solid_approval: 'Voted Yes', solid_disapproval: 'Voted No', unknown: 'Absent' },
    },
  ],
  entities: [
    {
      entity: { id: 'e-10', name: 'Alderperson Ten', entity_type: 'alderperson', district_name: 'Ward 10', jurisdiction_id: 'jur-1' },
      statuses: { 'project-1': { status: EntityStatus.SOLID_DISAPPROVAL, label: 'Voted No' } },
      aligned_count: 0,
      total_scoreable: 1,
    },
    {
      entity: { id: 'e-2', name: 'Alderperson Two', entity_type: 'alderperson', district_name: 'Ward 2', jurisdiction_id: 'jur-1' },
      statuses: { 'project-1': { status: EntityStatus.SOLID_APPROVAL, label: 'Voted Yes' } },
      aligned_count: 1,
      total_scoreable: 1,
    },
    {
      entity: { id: 'e-9', name: 'Alderperson Nine', entity_type: 'alderperson', district_name: 'Ward 9', jurisdiction_id: 'jur-1' },
      statuses: { 'project-1': { status: EntityStatus.UNKNOWN, label: 'Absent' } },
      aligned_count: 0,
      total_scoreable: 1,
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

  it('ward sort uses numeric ordering (Ward 2 before Ward 9 before Ward 10)', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: extendedScorecardResponse,
    } as never);
    renderScorecard();
    await screen.findByText('Alderperson Two');

    // Click Ward header to sort ascending by ward
    const wardSortLabel = screen.getByText('Ward');
    fireEvent.click(wardSortLabel);

    const rows = screen.getAllByRole('row');
    // rows[0] = header, rows[1..3] = data rows in order
    expect(rows[1]).toHaveTextContent('Ward 2');
    expect(rows[2]).toHaveTextContent('Ward 9');
    expect(rows[3]).toHaveTextContent('Ward 10');
  });

  it('ward sort descending puts Ward 10 first', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: extendedScorecardResponse,
    } as never);
    renderScorecard();
    await screen.findByText('Alderperson Two');

    const wardSortLabel = screen.getByText('Ward');
    fireEvent.click(wardSortLabel); // asc
    fireEvent.click(wardSortLabel); // desc

    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Ward 10');
  });

  it('clicking a project column header sorts by that project status', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: extendedScorecardResponse,
    } as never);
    renderScorecard();
    await screen.findByText('Alderperson Two');

    // Click the project column header — solid_approval (rank 0) sorts to top
    const projectSortLabel = screen.getByText('ADU Citywide Vote');
    fireEvent.click(projectSortLabel);

    const rows = screen.getAllByRole('row');
    // solid_approval entity (Alderperson Two, Ward 2) should be first
    expect(rows[1]).toHaveTextContent('Alderperson Two');
  });

  it('clicking a project column twice reverses the order', async () => {
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: extendedScorecardResponse,
    } as never);
    renderScorecard();
    await screen.findByText('Alderperson Two');

    const projectSortLabel = screen.getByText('ADU Citywide Vote');
    fireEvent.click(projectSortLabel); // asc: solid_approval first
    fireEvent.click(projectSortLabel); // desc: solid_disapproval first

    const rows = screen.getAllByRole('row');
    // unknown (rank 5) sorts last ascending, so first descending
    expect(rows[1]).toHaveTextContent('Alderperson Nine');
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

    // Click the Alignment sort label to toggle to ascending
    const scoreSortLabel = screen.getByText('Alignment');
    fireEvent.click(scoreSortLabel);

    const rowsAfterSort = screen.getAllByRole('row');
    const firstDataRowAfterSort = rowsAfterSort[1];
    expect(firstDataRowAfterSort).toHaveTextContent('Maria Hadden');
  });

  it('uses representative_title from data in entity column header', async () => {
    const senateScorecard: ScorecardResponse = {
      ...mockScorecardResponse,
      group_name: 'Abundant Housing Illinois — IL Senate',
      representative_title: 'Senator',
    };
    vi.mocked(scorecardService.getScorecard).mockResolvedValue({
      data: senateScorecard,
    } as never);
    renderScorecard();
    await screen.findByText('Maria Hadden');
    expect(screen.getByText('Senator')).toBeInTheDocument();
    expect(screen.queryByText('Alderperson')).not.toBeInTheDocument();
  });
});

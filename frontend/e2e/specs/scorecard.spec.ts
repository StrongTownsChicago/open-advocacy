import { test, expect, Page } from '@playwright/test';

const GROUP_SLUG = process.env.PLAYWRIGHT_SCORECARD_SLUG || 'strong-towns-chicago';
const SCORECARD_URL = `/scorecard/${GROUP_SLUG}`;

async function fetchScorecard(page: Page) {
  const res = await page.request.get(`/api/scorecard/${GROUP_SLUG}`);
  if (!res.ok()) return null;
  return res.json();
}

test.describe('Scorecard page', () => {
  test('skips gracefully when scorecard group is not seeded', async ({ page }) => {
    const res = await page.request.get(`/api/scorecard/${GROUP_SLUG}`);
    test.skip(res.ok(), 'Scorecard data is seeded — running full tests instead');

    // If the group doesn't exist, the API returns 404 and the page should show an error
    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');
    // Either an error heading or the generic "no scorecard data" message — something is visible
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 10000 });
  });

  test('renders the scorecard table with headers', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data || !data.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    // Group name appears in the heading
    await expect(page.getByRole('heading', { level: 4 }).first()).toContainText(data.group_name);

    // Fixed column headers
    await expect(page.getByRole('columnheader', { name: /ward/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /alderperson/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /score/i })).toBeVisible();

    // At least one project column header is visible
    const firstProject = data.projects[0];
    await expect(page.getByRole('columnheader').filter({ hasText: firstProject.title })).toBeVisible();
  });

  test('renders entity rows with ward and name', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data || !data.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    const firstEntity = data.entities[0].entity;
    // Entity name appears as a link to the representative detail page
    const nameLink = page.getByRole('link', { name: firstEntity.name });
    await expect(nameLink.first()).toBeVisible({ timeout: 10000 });
    await expect(nameLink.first()).toHaveAttribute('href', `/representatives/${firstEntity.id}`);

    // District name appears in the row
    if (firstEntity.district_name) {
      await expect(page.getByRole('cell', { name: firstEntity.district_name }).first()).toBeVisible();
    }
  });

  test('ward sort is numeric — Ward 2 appears before Ward 10', async ({ page }) => {
    const data = await fetchScorecard(page);
    const hasWard2 = data?.entities?.some((e: { entity: { district_name?: string } }) => e.entity.district_name === 'Ward 2');
    const hasWard10 = data?.entities?.some((e: { entity: { district_name?: string } }) => e.entity.district_name === 'Ward 10');
    test.skip(!hasWard2 || !hasWard10, 'Scorecard does not contain both Ward 2 and Ward 10 — skipping numeric sort test');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('link').first()).toBeVisible({ timeout: 10000 });

    // Click the Ward column header to sort ascending
    await page.getByRole('columnheader', { name: /ward/i }).click();

    // Collect all ward cells (first column in each data row)
    const wardCells = page.getByRole('row').filter({ hasNot: page.getByRole('columnheader') })
      .getByRole('cell').nth(0);

    // The first visible ward cell after sorting should be Ward 2, not Ward 10
    const firstWardText = await page.getByRole('row').nth(1).getByRole('cell').nth(0).textContent();
    expect(firstWardText).not.toBe('Ward 10');

    // Ward 2 row should come before Ward 10 row
    const allRows = page.getByRole('row');
    const rowCount = await allRows.count();
    let ward2Index = -1;
    let ward10Index = -1;
    for (let i = 1; i < rowCount; i++) {
      const cellText = await allRows.nth(i).getByRole('cell').nth(0).textContent();
      if (cellText === 'Ward 2') ward2Index = i;
      if (cellText === 'Ward 10') ward10Index = i;
    }
    expect(ward2Index).toBeGreaterThan(0);
    expect(ward10Index).toBeGreaterThan(0);
    expect(ward2Index).toBeLessThan(ward10Index);
    // Suppress unused variable warning
    void wardCells;
  });

  test('clicking Score header toggles sort direction', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data || data.entities?.length < 2, 'Need at least 2 entities to test sort');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('link').first()).toBeVisible({ timeout: 10000 });

    // Default is score descending — record first row name
    const firstRowDesc = await page.getByRole('row').nth(1).textContent();

    // Click Score to flip to ascending
    await page.getByRole('columnheader', { name: /score/i }).click();
    await page.waitForTimeout(100);

    const firstRowAsc = await page.getByRole('row').nth(1).textContent();

    // With 2+ entities having different scores the order should differ
    const scores = data.entities.map((e: { aligned_count: number; total_scoreable: number }) =>
      e.total_scoreable > 0 ? e.aligned_count / e.total_scoreable : 0
    );
    const allSame = scores.every((s: number) => s === scores[0]);
    if (!allSame) {
      expect(firstRowAsc).not.toBe(firstRowDesc);
    }
  });

  test('clicking a project column header sorts rows by status', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data || !data.projects?.length || data.entities?.length < 2, 'Need projects and 2+ entities');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('link').first()).toBeVisible({ timeout: 10000 });

    const firstProject = data.projects[0];

    // Record row order before clicking
    const rowsBefore = await page.getByRole('row').nth(1).textContent();

    // Click the first project column header
    await page.getByRole('columnheader').filter({ hasText: firstProject.title }).click();
    await page.waitForTimeout(100);

    // The sort label for this project column should now be active
    const projectHeader = page.getByRole('columnheader').filter({ hasText: firstProject.title });
    await expect(projectHeader).toBeVisible();

    // Click again to reverse direction — rows should update
    await page.getByRole('columnheader').filter({ hasText: firstProject.title }).click();
    await page.waitForTimeout(100);

    const rowsAfterDoubleClick = await page.getByRole('row').nth(1).textContent();

    // After two clicks the first row should differ from the initial sort by score
    // (as long as entities have varied statuses for this project)
    const statuses = data.entities.map((e: { statuses: Record<string, { status: string }> }) =>
      e.statuses[firstProject.id]?.status
    );
    const allSameStatus = statuses.every((s: string) => s === statuses[0]);
    if (!allSameStatus) {
      expect(rowsAfterDoubleClick).not.toBe(rowsBefore);
    }
  });

  test('alignment score is shown as "X / Y" format', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data || !data.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    const firstEntity = data.entities[0];
    const scoreText = `${firstEntity.aligned_count} / ${firstEntity.total_scoreable}`;
    await expect(page.getByText(scoreText, { exact: true }).first()).toBeVisible({ timeout: 10000 });
  });
});

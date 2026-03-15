import { test, expect, Page } from '@playwright/test';

const GROUP_SLUG = process.env.PLAYWRIGHT_SCORECARD_SLUG || 'strong-towns-chicago';
const SCORECARD_URL = `/scorecard/${GROUP_SLUG}`;

async function fetchScorecard(page: Page) {
  const res = await page.request.get(`/api/scorecard/${GROUP_SLUG}`);
  if (!res.ok()) return null;
  return res.json();
}

test.describe('Scorecard mobile view', () => {
  // All tests in this describe block run at a mobile viewport
  test.use({ viewport: { width: 390, height: 844 } });

  test('renders card list — no table headers visible on mobile', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');
    // Wait for content to appear
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 10000 });

    // Desktop table column headers must not be visible at mobile width
    await expect(page.getByRole('columnheader', { name: /ward/i })).not.toBeVisible();
    await expect(page.getByRole('columnheader', { name: /alderperson/i })).not.toBeVisible();
    await expect(page.getByRole('columnheader', { name: /score/i })).not.toBeVisible();
  });

  test('entity name links are visible in card format', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    const firstEntity = data.entities[0].entity;
    const nameLink = page.getByRole('link', { name: firstEntity.name }).first();
    await expect(nameLink).toBeVisible({ timeout: 10000 });
    await expect(nameLink).toHaveAttribute('href', `/representatives/${firstEntity.id}`);
  });

  test('score is shown in "Score: X / Y" caption format on mobile cards', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    const firstRow = data.entities[0];
    const scoreText = `Score: ${firstRow.aligned_count} / ${firstRow.total_scoreable}`;
    await expect(page.getByText(scoreText, { exact: true }).first()).toBeVisible({ timeout: 10000 });
  });

  test('project status chips are visible inside entity cards', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length || !data?.projects?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    // Each entity card lists project titles as links — at least one must appear
    const firstProject = data.projects[0];
    await expect(
      page.getByRole('link', { name: firstProject.title }).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('entity name link navigates to entity detail on mobile', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(SCORECARD_URL);
    await page.waitForLoadState('networkidle');

    const firstEntity = data.entities[0].entity;
    await page.getByRole('link', { name: firstEntity.name }).first().click();
    await expect(page).toHaveURL(`/representatives/${firstEntity.id}`);
  });
});

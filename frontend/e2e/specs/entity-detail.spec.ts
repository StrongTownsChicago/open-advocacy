import { test, expect, Page } from '@playwright/test';

const GROUP_SLUG = process.env.PLAYWRIGHT_SCORECARD_SLUG || 'strong-towns-chicago';

async function fetchScorecard(page: Page) {
  const res = await page.request.get(`/api/scorecard/${GROUP_SLUG}`);
  if (!res.ok()) return null;
  return res.json();
}

test.describe('Entity detail page', () => {
  test('loads entity name and sections from a direct URL', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    const firstEntity = data.entities[0].entity;
    await page.goto(`/representatives/${firstEntity.id}`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: firstEntity.name })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Contact Information')).toBeVisible();
    await expect(page.getByText('Projects & Positions')).toBeVisible();
  });

  test('shows project cards with View Project button for entities with status records', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    // Find an entity that has at least one status entry
    const entityWithStatus = data.entities.find(
      (e: { statuses: Record<string, unknown> }) => Object.keys(e.statuses).length > 0
    );
    test.skip(!entityWithStatus, 'No entities with status records — skipping');

    await page.goto(`/representatives/${entityWithStatus.entity.id}`);
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('button', { name: 'View Project' }).first()).toBeVisible({ timeout: 10000 });
  });

  test('"View Project" navigates to the project detail page', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    const entityWithStatus = data.entities.find(
      (e: { statuses: Record<string, unknown> }) => Object.keys(e.statuses).length > 0
    );
    test.skip(!entityWithStatus, 'No entities with status records — skipping');

    await page.goto(`/representatives/${entityWithStatus.entity.id}`);
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: 'View Project' }).first().click();
    await expect(page).toHaveURL(/\/projects\//);
  });

  test('clicking entity name link on scorecard navigates to entity detail', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    await page.goto(`/scorecard/${GROUP_SLUG}`);
    await page.waitForLoadState('networkidle');

    const firstEntity = data.entities[0].entity;
    const nameLink = page.getByRole('link', { name: firstEntity.name }).first();
    await expect(nameLink).toBeVisible({ timeout: 10000 });
    await nameLink.click();

    await expect(page).toHaveURL(`/representatives/${firstEntity.id}`);
    await expect(page.getByRole('heading', { name: firstEntity.name })).toBeVisible({ timeout: 10000 });
  });

  test('Back button returns to previous page', async ({ page }) => {
    const data = await fetchScorecard(page);
    test.skip(!data?.entities?.length, 'Scorecard not seeded — skipping');

    const firstEntity = data.entities[0].entity;

    // Navigate from scorecard → entity detail
    await page.goto(`/scorecard/${GROUP_SLUG}`);
    await page.waitForLoadState('networkidle');
    await page.getByRole('link', { name: firstEntity.name }).first().click();
    await expect(page).toHaveURL(`/representatives/${firstEntity.id}`);

    await page.getByRole('button', { name: 'Back' }).click();
    await expect(page).toHaveURL(new RegExp(`/scorecard/${GROUP_SLUG}`));
  });
});

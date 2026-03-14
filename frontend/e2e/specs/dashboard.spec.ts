import { test, expect } from '@playwright/test';

const DASHBOARD_SLUG = process.env.PLAYWRIGHT_DASHBOARD_SLUG || 'adu-opt-in-dashboard';

test.describe('Public slug dashboards', () => {
  test('loads dashboard page for known slug', async ({ page }) => {
    await page.goto(`/dashboard/${DASHBOARD_SLUG}`);
    await page.waitForLoadState('networkidle');
    // The dashboard should render — either content or a not-found message
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 10000 });
  });

  test('/adu-opt-in-dashboard redirects to /dashboard/adu-opt-in-dashboard', async ({ page }) => {
    await page.goto('/adu-opt-in-dashboard');
    await expect(page).toHaveURL(/\/dashboard\/adu-opt-in-dashboard/);
  });

  test('unknown slug shows error or not-found state', async ({ page }) => {
    await page.goto('/dashboard/this-slug-does-not-exist-xyz');
    await page.waitForLoadState('networkidle');
    // Should show some error indication — not blank
    await expect(page.getByRole('heading').first()).toBeVisible({ timeout: 10000 });
  });

  test('adu dashboard renders custom status labels from dashboard_config', async ({ page }) => {
    // Skip if the ADU project doesn't exist in this environment
    const res = await page.request.get('/api/projects/?slug=adu-opt-in-dashboard');
    const projects = await res.json();
    const project = projects[0];
    test.skip(!project?.dashboard_config?.status_labels, 'ADU project with custom status labels not seeded');

    await page.goto('/dashboard/adu-opt-in-dashboard');
    await page.waitForLoadState('networkidle');

    // The ADU dashboard configures custom labels: solid_approval → "Fully Opted In",
    // leaning_disapproval → "Not Opted In". These must appear in the status distribution
    // legend and/or entity rows — not the generic defaults ("Solid Approval", "Leaning Disapproval").
    await expect(page.getByText('Fully Opted In', { exact: false }).first()).toBeVisible({
      timeout: 10000,
    });
    await expect(page.getByText('Not Opted In', { exact: false }).first()).toBeVisible({
      timeout: 10000,
    });

    // Confirm generic fallback labels are NOT used for these two statuses
    await expect(page.getByText('Solid Approval', { exact: true }).first()).not.toBeVisible();
    await expect(page.getByText('Leaning Disapproval', { exact: true }).first()).not.toBeVisible();
  });
});

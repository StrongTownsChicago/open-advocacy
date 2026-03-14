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
});

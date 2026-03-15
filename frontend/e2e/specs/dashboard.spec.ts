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

test.describe('ADU dashboard search and status filter', () => {
  test('search box narrows entity rows and clearing restores them', async ({ page }) => {
    const res = await page.request.get('/api/projects/?slug=adu-opt-in-dashboard');
    const projects = await res.json();
    test.skip(!projects?.[0], 'ADU project not seeded — skipping');

    await page.goto('/dashboard/adu-opt-in-dashboard');
    await page.waitForLoadState('networkidle');

    const searchInput = page.getByPlaceholder('Search entities...');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    // Type a term that matches nothing
    await searchInput.fill('zzz_no_match_zzz');
    await expect(
      page.getByText('No entities found matching your criteria')
    ).toBeVisible({ timeout: 5000 });

    // Clear the search — entities should come back
    await searchInput.clear();
    await expect(
      page.getByText('No entities found matching your criteria')
    ).not.toBeVisible({ timeout: 5000 });
  });

  test('status filter uses custom ADU labels and filters rows', async ({ page }) => {
    const res = await page.request.get('/api/projects/?slug=adu-opt-in-dashboard');
    const projects = await res.json();
    test.skip(!projects?.[0]?.dashboard_config?.status_labels, 'ADU project with custom labels not seeded — skipping');

    await page.goto('/dashboard/adu-opt-in-dashboard');
    await page.waitForLoadState('networkidle');

    // The Status dropdown must use the custom label for solid_approval
    await page.getByRole('combobox', { name: /status/i }).click();
    await expect(page.getByRole('option', { name: 'Fully Opted In' })).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole('option', { name: 'Not Opted In' })).toBeVisible();

    // Select "Fully Opted In" and verify the filter applies
    await page.getByRole('option', { name: 'Fully Opted In' }).click();

    // Either some filtered rows remain, or the "no entities" message appears
    const noMatch = page.getByText('No entities found matching your criteria');
    const rowsVisible = page.getByRole('row').filter({ hasNot: page.getByRole('columnheader') });
    const hasRows = (await rowsVisible.count()) > 0;
    const hasNoMatch = await noMatch.isVisible();
    expect(hasRows || hasNoMatch).toBe(true);

    // Reset to All Statuses
    await page.getByRole('combobox', { name: /status/i }).click();
    await page.getByRole('option', { name: 'All Statuses' }).click();
    await expect(page.getByText('No entities found matching your criteria')).not.toBeVisible({ timeout: 5000 });
  });

  test('search and status filter work together', async ({ page }) => {
    const res = await page.request.get('/api/projects/?slug=adu-opt-in-dashboard');
    const projects = await res.json();
    test.skip(!projects?.[0]?.dashboard_config?.status_labels, 'ADU project with custom labels not seeded — skipping');

    await page.goto('/dashboard/adu-opt-in-dashboard');
    await page.waitForLoadState('networkidle');

    const searchInput = page.getByPlaceholder('Search entities...');
    await expect(searchInput).toBeVisible({ timeout: 10000 });

    // Apply status filter first
    await page.getByRole('combobox', { name: /status/i }).click();
    await page.getByRole('option', { name: 'Fully Opted In' }).click();

    // Then apply a non-matching search on top — "no match" must appear
    await searchInput.fill('zzz_no_match_zzz');
    await expect(
      page.getByText('No entities found matching your criteria')
    ).toBeVisible({ timeout: 5000 });

    // Clearing just the search should restore the status-filtered results
    await searchInput.clear();
    await expect(
      page.getByText('No entities found matching your criteria')
    ).not.toBeVisible({ timeout: 5000 });
  });
});

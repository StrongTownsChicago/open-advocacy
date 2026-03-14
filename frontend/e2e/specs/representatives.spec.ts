import { test, expect } from '@playwright/test';

const skipGeo = process.env.PLAYWRIGHT_SKIP_GEO_TESTS === 'true';
const TEST_ADDRESS = '121 N LaSalle St, Chicago, IL 60602';

test.describe('Representative lookup', () => {
  test('page heading and address input are visible', async ({ page }) => {
    await page.goto('/representatives');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Find Your Representatives' })).toBeVisible();
    await expect(page.getByLabel('Street Address')).toBeVisible();
  });

  test('entering address and submitting shows results', async ({ page }) => {
    test.skip(skipGeo, 'Set PLAYWRIGHT_SKIP_GEO_TESTS=true to skip geo tests');
    await page.goto('/representatives');
    await page.waitForLoadState('networkidle');

    await page.getByLabel('Street Address').fill(TEST_ADDRESS);
    await page.getByRole('button', { name: 'Find Representatives' }).click();

    // Wait for loading to finish
    await expect(page.getByRole('button', { name: 'Searching...' })).toBeHidden({ timeout: 15000 });
    await expect(page.getByRole('heading', { name: 'Your Representatives' })).toBeVisible();
  });

  test('View Representative Details navigates to entity detail', async ({ page }) => {
    test.skip(skipGeo, 'Set PLAYWRIGHT_SKIP_GEO_TESTS=true to skip geo tests');
    await page.goto('/representatives');
    await page.waitForLoadState('networkidle');

    await page.getByLabel('Street Address').fill(TEST_ADDRESS);
    await page.getByRole('button', { name: 'Find Representatives' }).click();

    // Wait for search to complete
    await expect(page.getByRole('button', { name: 'Searching...' })).toBeHidden({ timeout: 15000 });

    // Dismiss the "Done viewing?" dialog if it appears
    const stayButton = page.getByRole('button', { name: 'Stay' });
    if (await stayButton.isVisible()) {
      await stayButton.click();
    }

    const detailButton = page.getByRole('button', { name: 'View Representative Details' }).first();
    await expect(detailButton).toBeVisible({ timeout: 5000 });
    await detailButton.click();
    await expect(page).toHaveURL(/\/representatives\//);
  });
});

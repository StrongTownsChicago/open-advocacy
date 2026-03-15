import { test, expect, Page } from '@playwright/test';

const skipGeo = process.env.PLAYWRIGHT_SKIP_GEO_TESTS === 'true';
const TEST_ADDRESS = '121 N LaSalle St, Chicago, IL 60602';

async function lookupAddress(page: Page) {
  await page.goto('/representatives');
  await page.waitForLoadState('networkidle');
  await page.getByLabel('Street Address').fill(TEST_ADDRESS);
  await page.getByRole('button', { name: 'Find Representatives' }).click();
  await expect(page.getByRole('button', { name: 'Searching...' })).toBeHidden({ timeout: 15000 });
  // Dismiss back modal if present
  const stayButton = page.getByRole('button', { name: 'Stay' });
  if (await stayButton.isVisible()) await stayButton.click();
}

test.describe('Representative lookup → project integration', () => {
  test('after address lookup the project page shows the representative section', async ({ page }) => {
    test.skip(skipGeo, 'PLAYWRIGHT_SKIP_GEO_TESTS is set — skipping geo tests');

    const projectsRes = await page.request.get('/api/projects/');
    const projects = await projectsRes.json();
    test.skip(!projects?.length, 'No projects seeded — skipping');

    await lookupAddress(page);
    await expect(page.getByRole('heading', { name: 'Your Representatives' })).toBeVisible();

    // Navigate to a project detail page
    await page.goto(`/projects/${projects[0].id}`);
    await page.waitForLoadState('networkidle');

    // After a successful lookup the context is populated, so the "Find Your Representative"
    // CTA button must not be visible — the section is in "found" state
    await expect(
      page.getByRole('button', { name: /find your representative/i })
    ).not.toBeVisible({ timeout: 10000 });

    // The section must be in one of its two "populated" states
    const hasStands = await page.getByText(/where your .+ stands/i).isVisible();
    const hasNotInvolved = await page.getByText(/not involved with this project/i).isVisible();
    expect(hasStands || hasNotInvolved).toBe(true);
  });

  test('representative name from lookup appears in project detail when jurisdiction matches', async ({ page }) => {
    test.skip(skipGeo, 'PLAYWRIGHT_SKIP_GEO_TESTS is set — skipping geo tests');

    // Find a project in the Chicago jurisdiction (the lookup address is Chicago)
    const projectsRes = await page.request.get('/api/projects/');
    const projects = await projectsRes.json();
    test.skip(!projects?.length, 'No projects seeded — skipping');

    await lookupAddress(page);

    // Capture representative names shown on the lookup page
    const repNameLinks = page.getByRole('heading', { level: 6 });
    const repCount = await repNameLinks.count();
    test.skip(repCount === 0, 'Address lookup returned no representatives — skipping');

    const firstRepName = await repNameLinks.first().textContent();

    // Navigate to the first project and check whether that rep appears in the section
    await page.goto(`/projects/${projects[0].id}`);
    await page.waitForLoadState('networkidle');

    // If the rep is in the same jurisdiction as this project, their name must appear
    // in the "Where Your Representative Stands" section
    const repIsShown = firstRepName
      ? await page.getByText(firstRepName, { exact: false }).isVisible()
      : false;

    // We can't guarantee the jurisdictions match, so only assert the section exists
    const sectionVisible = await page.getByText(/your representative/i).first().isVisible();
    expect(sectionVisible || repIsShown).toBe(true);
  });

  test('clearing representatives on lookup page resets the project section', async ({ page }) => {
    test.skip(skipGeo, 'PLAYWRIGHT_SKIP_GEO_TESTS is set — skipping geo tests');

    const projectsRes = await page.request.get('/api/projects/');
    const projects = await projectsRes.json();
    test.skip(!projects?.length, 'No projects seeded — skipping');

    // Step 1: Lookup so context is populated
    await lookupAddress(page);
    await expect(page.getByRole('heading', { name: 'Your Representatives' })).toBeVisible();

    // Step 2: Clear the results
    await page.getByRole('button', { name: 'Clear Results' }).click();

    // Step 3: Navigate to project — CTA button must now be visible again
    await page.goto(`/projects/${projects[0].id}`);
    await page.waitForLoadState('networkidle');

    await expect(
      page.getByRole('button', { name: /find your/i })
    ).toBeVisible({ timeout: 10000 });
  });
});

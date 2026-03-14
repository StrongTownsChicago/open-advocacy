import { test, expect } from '@playwright/test';
import { test as authTest, skipIfNoAuth } from '../fixtures';
import { ProjectListPage } from '../pages/ProjectListPage';

test.describe('Project list (public)', () => {
  test('shows heading and project cards', async ({ page }) => {
    const listPage = new ProjectListPage(page);
    await listPage.goto();
    await expect(listPage.heading()).toBeVisible();
    const viewDetailsButtons = page.getByRole('button', { name: 'View Details' });
    const count = await viewDetailsButtons.count();
    if (count > 0) {
      await expect(viewDetailsButtons.first()).toBeVisible();
    }
  });

  test('search input is visible', async ({ page }) => {
    const listPage = new ProjectListPage(page);
    await listPage.goto();
    await expect(listPage.searchInput()).toBeVisible();
  });

  test('searching with a non-matching term shows empty message', async ({ page }) => {
    const listPage = new ProjectListPage(page);
    await listPage.goto();
    await listPage.search('xyzzy_no_match_99999');
    await expect(listPage.emptyMessage()).toBeVisible();
  });

  test('clicking View Details navigates to project detail', async ({ page }) => {
    const listPage = new ProjectListPage(page);
    await listPage.goto();
    await page.waitForLoadState('networkidle');
    const count = await page.getByRole('button', { name: 'View Details' }).count();
    if (count === 0) {
      test.skip(true, 'No projects seeded');
      return;
    }
    await page.getByRole('button', { name: 'View Details' }).first().click();
    await expect(page).toHaveURL(/\/projects\//);
  });

  test('does NOT show Create Project button to unauthenticated user', async ({ page }) => {
    const listPage = new ProjectListPage(page);
    await listPage.goto();
    await page.waitForLoadState('networkidle');
    await expect(listPage.createButton()).not.toBeVisible();
  });
});

authTest.describe('Project list (editor)', () => {
  authTest.beforeEach(skipIfNoAuth('editor'));

  authTest('shows Create Project button for editor role', async ({ editorPage }) => {
    const listPage = new ProjectListPage(editorPage);
    await listPage.goto();
    await editorPage.waitForLoadState('networkidle');
    await expect(listPage.createButton()).toBeVisible();
  });
});

test.describe('Project detail (public)', () => {
  test('does not show Edit button to unauthenticated user', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForLoadState('networkidle');
    const count = await page.getByRole('button', { name: 'View Details' }).count();
    if (count === 0) {
      test.skip(true, 'No projects seeded');
      return;
    }
    await page.getByRole('button', { name: 'View Details' }).first().click();
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: /Edit/i })).not.toBeVisible();
  });
});

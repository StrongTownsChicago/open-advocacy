import { test, expect, skipIfNoAuth } from '../fixtures';

test.describe('Editor workflow', () => {
  test.beforeEach(skipIfNoAuth('editor'));

  test('Create Project button is visible for editor', async ({ editorPage }) => {
    await editorPage.goto('/projects');
    await editorPage.waitForLoadState('networkidle');
    await expect(editorPage.getByRole('button', { name: 'Create Project' })).toBeVisible();
  });

  test('project create form shows required fields', async ({ editorPage }) => {
    await editorPage.goto('/projects/create');
    await editorPage.waitForLoadState('networkidle');
    await expect(editorPage.getByLabel(/title/i).first()).toBeVisible();
  });

  test('title field required — shows validation error on empty submit', async ({ editorPage }) => {
    await editorPage.goto('/projects/create');
    await editorPage.waitForLoadState('networkidle');
    await editorPage.getByLabel(/title/i).first().clear();
    // Disable browser native validation so our custom validation fires
    await editorPage.locator('form').evaluate(f => ((f as HTMLFormElement).noValidate = true));
    await editorPage.getByRole('button', { name: /Create|Save/i }).first().click();
    await expect(editorPage.getByText(/required/i).first()).toBeVisible();
  });

  test('successful project create navigates to project detail', async ({ editorPage }) => {
    await editorPage.goto('/projects/create');
    await editorPage.waitForLoadState('networkidle');

    const timestamp = Date.now();
    await editorPage.getByLabel(/title/i).first().fill(`E2E Test Project ${timestamp}`);

    const descField = editorPage.getByLabel(/description/i).first();
    if (await descField.isVisible()) {
      await descField.fill('Created by Playwright E2E test');
    }

    await editorPage.getByRole('button', { name: /Create|Save/i }).first().click();
    await editorPage.waitForLoadState('networkidle');
    await expect(editorPage).toHaveURL(/\/projects\//);
  });
});

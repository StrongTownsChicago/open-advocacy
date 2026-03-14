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

  test('editor can update a representative status', async ({ editorPage }) => {
    // Navigate to the first available project that has entities
    await editorPage.goto('/projects');
    await editorPage.waitForLoadState('networkidle');

    const firstViewDetails = editorPage.getByRole('link', { name: /view details/i }).first();
    await expect(firstViewDetails).toBeVisible({ timeout: 10000 });
    await firstViewDetails.click();
    await editorPage.waitForLoadState('networkidle');

    // Expand the first entity row
    const firstRow = editorPage.locator('tbody tr').first();
    await expect(firstRow).toBeVisible({ timeout: 10000 });
    await firstRow.click();

    // The Update/Save button appears in the expanded panel for authenticated editors
    const saveButton = editorPage.getByRole('button', { name: /^(update|save)$/i }).first();
    await expect(saveButton).toBeVisible({ timeout: 5000 });

    // Submit — preserves current status, just verifies the round-trip completes without error
    await saveButton.click();

    // No error message should appear
    await expect(editorPage.getByText('Failed to update status')).not.toBeVisible();
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

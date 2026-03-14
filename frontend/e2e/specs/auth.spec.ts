import { test, expect } from '@playwright/test';
import { skipIfNoAuth } from '../fixtures';
import { LoginPage } from '../pages/LoginPage';

test.describe('Auth flows (public)', () => {
  test('login form shows email, password, and Sign In button', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await expect(loginPage.emailInput()).toBeVisible();
    await expect(loginPage.passwordInput()).toBeVisible();
    await expect(loginPage.submitButton()).toBeVisible();
  });

  test('shows "Invalid email format" error for malformed email', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    // Both fields need values so browser native validation doesn't block the email check
    await loginPage.emailInput().fill('notanemail');
    await loginPage.passwordInput().fill('somepassword');
    await loginPage.submitButton().click();
    await expect(page.getByText('Invalid email format')).toBeVisible();
  });

  test('shows "Password is required" when password is omitted', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.emailInput().fill('user@example.com');
    // Disable browser native HTML5 validation so our custom validation fires
    await page.locator('form').evaluate(f => ((f as HTMLFormElement).noValidate = true));
    await loginPage.submitButton().click();
    await expect(page.getByText('Password is required')).toBeVisible();
  });

  test('shows server error alert on wrong credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('nobody@example.com', 'wrongpassword');
    await expect(loginPage.errorAlert()).toBeVisible();
  });

  test('redirects unauthenticated user from /admin to /login', async ({ page }) => {
    await page.goto('/admin');
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('Auth flows (authenticated)', () => {
  test.beforeEach(skipIfNoAuth('super-admin'));

  test('logout clears auth state and blocks /admin', async ({ browser }) => {
    const { fileURLToPath } = await import('url');
    const { default: path } = await import('path');
    const { default: fs } = await import('fs');

    const authFile = path.join(
      path.dirname(fileURLToPath(import.meta.url)),
      '../.auth/super-admin.json'
    );
    const ctx = await browser.newContext({ storageState: authFile });
    const page = await ctx.newPage();

    await page.goto('/projects');
    await page.waitForLoadState('networkidle');

    // Simulate logout by clearing localStorage
    await page.evaluate(() => {
      localStorage.removeItem('open_advocacy_auth_token');
      localStorage.removeItem('open_advocacy_user');
    });

    await page.goto('/admin');
    await expect(page).toHaveURL(/\/login/);
    await ctx.close();
  });
});

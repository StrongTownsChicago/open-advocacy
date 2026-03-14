import { test, expect } from '../fixtures';
import { skipIfNoAuth } from '../fixtures';

test.describe('Admin dashboard (group_admin)', () => {
  test.beforeEach(skipIfNoAuth('admin'));

  test('accessible and shows dashboard heading', async ({ adminPage }) => {
    await adminPage.goto('/admin');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByRole('heading', { name: 'Admin Dashboard' })).toBeVisible();
  });

  test('User Management and Register User cards are visible', async ({ adminPage }) => {
    await adminPage.goto('/admin');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('User Management')).toBeVisible();
    await expect(adminPage.getByText('Register User')).toBeVisible();
  });

  test('Data Imports card is NOT visible to group_admin', async ({ adminPage }) => {
    await adminPage.goto('/admin');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('Data Imports')).not.toBeVisible();
  });

  test('clicking User Management navigates to /admin/users', async ({ adminPage }) => {
    await adminPage.goto('/admin');
    await adminPage.waitForLoadState('networkidle');
    await adminPage.getByText('User Management').click();
    await expect(adminPage).toHaveURL(/\/admin\/users/);
  });

  test('/admin/imports redirects group_admin to /unauthorized', async ({ adminPage }) => {
    await adminPage.goto('/admin/imports');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage).toHaveURL(/\/unauthorized/);
  });
});

test.describe('Admin dashboard (super_admin)', () => {
  test.beforeEach(skipIfNoAuth('super-admin'));

  test('Data Imports card IS visible to super_admin', async ({ superAdminPage }) => {
    await superAdminPage.goto('/admin');
    await superAdminPage.waitForLoadState('networkidle');
    await expect(superAdminPage.getByText('Data Imports')).toBeVisible();
  });

  test('/admin/imports accessible to super_admin', async ({ superAdminPage }) => {
    await superAdminPage.goto('/admin/imports');
    await superAdminPage.waitForLoadState('networkidle');
    await expect(superAdminPage).not.toHaveURL(/\/unauthorized/);
    await expect(superAdminPage.getByRole('heading').first()).toBeVisible();
  });
});

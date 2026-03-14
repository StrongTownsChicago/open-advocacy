import { Page } from '@playwright/test';

export class AdminDashboardPage {
  constructor(private page: Page) {}

  heading = () => this.page.getByRole('heading', { name: 'Admin Dashboard' });
  userManagementCard = () => this.page.getByText('User Management');
  dataImportsCard = () => this.page.getByText('Data Imports');
  registerUserCard = () => this.page.getByText('Register User');

  async goto() {
    await this.page.goto('/admin');
    await this.heading().waitFor();
  }
}

import { Page } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  emailInput = () => this.page.getByLabel('Email Address');
  passwordInput = () => this.page.getByLabel('Password');
  submitButton = () => this.page.getByRole('button', { name: 'Sign In' });
  errorAlert = () => this.page.getByRole('alert');

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput().fill(email);
    await this.passwordInput().fill(password);
    await this.submitButton().click();
  }
}

import { Page } from '@playwright/test';

export class ProjectListPage {
  constructor(private page: Page) {}

  heading = () => this.page.getByRole('heading', { name: 'Advocacy Projects' });
  // InputBase with placeholder (not a labeled TextField)
  searchInput = () => this.page.getByPlaceholder('Search projects');
  // MUI Select uses aria-label on the hidden input
  statusFilter = () => this.page.getByRole('combobox', { name: 'Filter by Status' });
  createButton = () => this.page.getByRole('button', { name: 'Create Project' });
  emptyMessage = () => this.page.getByText('No projects found matching your criteria');

  async goto() {
    await this.page.goto('/projects');
  }

  async search(term: string) {
    await this.searchInput().fill(term);
    // Wait for debounce (500ms) + network to settle
    await this.page.waitForLoadState('networkidle');
  }
}

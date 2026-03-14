import { Page } from '@playwright/test';

export class ProjectDetailPage {
  constructor(private page: Page) {}

  editButton = () => this.page.getByRole('button', { name: /Edit/i });
  statusDistributionTab = () => this.page.getByRole('tab', { name: /Status Distribution/i });
  entityListTab = () => this.page.getByRole('tab', { name: /Representatives|Entity List/i });
  mapTab = () => this.page.getByRole('tab', { name: /Map/i });

  async goto(id: string) {
    await this.page.goto(`/projects/${id}`);
  }
}

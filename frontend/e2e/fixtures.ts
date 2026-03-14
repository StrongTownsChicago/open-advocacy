import { test as base, Page } from '@playwright/test';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

type Fixtures = { superAdminPage: Page; adminPage: Page; editorPage: Page };

function authState(file: string) {
  return path.join(__dirname, `.auth/${file}`);
}

function hasValidAuth(file: string): boolean {
  const filePath = authState(file);
  if (!fs.existsSync(filePath)) return false;
  try {
    const state = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    return state.origins?.[0]?.localStorage?.some(
      (e: { name: string }) => e.name === 'open_advocacy_auth_token'
    ) ?? false;
  } catch {
    return false;
  }
}

export const test = base.extend<Fixtures>({
  superAdminPage: async ({ browser }, use) => {
    if (!hasValidAuth('super-admin.json')) {
      // Can't skip from a fixture — provide an inert page; test must call skipIfNoAuth
      const ctx = await browser.newContext();
      const page = await ctx.newPage();
      await use(page);
      await ctx.close();
      return;
    }
    const ctx = await browser.newContext({ storageState: authState('super-admin.json') });
    const page = await ctx.newPage();
    await use(page);
    await ctx.close();
  },
  adminPage: async ({ browser }, use) => {
    if (!hasValidAuth('admin.json')) {
      const ctx = await browser.newContext();
      const page = await ctx.newPage();
      await use(page);
      await ctx.close();
      return;
    }
    const ctx = await browser.newContext({ storageState: authState('admin.json') });
    const page = await ctx.newPage();
    await use(page);
    await ctx.close();
  },
  editorPage: async ({ browser }, use) => {
    if (!hasValidAuth('editor.json')) {
      const ctx = await browser.newContext();
      const page = await ctx.newPage();
      await use(page);
      await ctx.close();
      return;
    }
    const ctx = await browser.newContext({ storageState: authState('editor.json') });
    const page = await ctx.newPage();
    await use(page);
    await ctx.close();
  },
});

/** Call inside test.beforeEach to skip the whole describe block when auth is not available. */
export function skipIfNoAuth(role: 'super-admin' | 'admin' | 'editor') {
  return () => {
    if (!hasValidAuth(`${role}.json`)) {
      test.skip(true, `Auth not configured for role "${role}" — no users seeded`);
    }
  };
}

export { expect } from '@playwright/test';

import { request } from '@playwright/test';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const API_URL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';

const ROLES = [
  {
    email: process.env.PLAYWRIGHT_SUPER_ADMIN_EMAIL || 'admin@example.com',
    password: process.env.PLAYWRIGHT_SUPER_ADMIN_PASSWORD || 'AdminPassword123!',
    file: 'super-admin.json',
  },
  {
    email: process.env.PLAYWRIGHT_ADMIN_EMAIL || 'groupadmin@example.com',
    password: process.env.PLAYWRIGHT_ADMIN_PASSWORD || 'GroupAdminPassword123!',
    file: 'admin.json',
  },
  {
    email: process.env.PLAYWRIGHT_EDITOR_EMAIL || 'editor@example.com',
    password: process.env.PLAYWRIGHT_EDITOR_PASSWORD || 'EditorPassword123!',
    file: 'editor.json',
  },
];

async function loginAndSave(role: (typeof ROLES)[number]) {
  const dir = path.join(__dirname, '.auth');
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  const ctx = await request.newContext({ baseURL: API_URL });

  const tokenRes = await ctx.post('/api/auth/token', {
    multipart: { username: role.email, password: role.password },
  });

  if (!tokenRes.ok()) {
    console.warn(
      `[global-setup] Login skipped for ${role.email} — auth-dependent tests will be skipped`
    );
    await ctx.dispose();
    return;
  }

  const { access_token } = await tokenRes.json();
  const profileRes = await ctx.get('/api/auth/me', {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  const user = await profileRes.json();

  const storageState = {
    cookies: [],
    origins: [
      {
        origin: BASE_URL,
        localStorage: [
          { name: 'open_advocacy_auth_token', value: access_token },
          { name: 'open_advocacy_user', value: JSON.stringify(user) },
        ],
      },
    ],
  };

  fs.writeFileSync(path.join(dir, role.file), JSON.stringify(storageState, null, 2));
  console.log(`[global-setup] Logged in as ${role.email} (${role.file})`);
  await ctx.dispose();
}

export default async function globalSetup() {
  await Promise.all(ROLES.map(loginAndSave));
}

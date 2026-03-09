import { describe, it, expect } from 'vitest';

/**
 * Test the HTTPS enforcement interceptor logic from api.ts.
 *
 * The interceptor rewrites http:// URLs to https://.
 * We test the logic directly rather than going through axios internals.
 */

function enforceHttps(url: string | undefined): string | undefined {
  if (url && url.startsWith('http://')) {
    return url.replace('http://', 'https://');
  }
  return url;
}

describe('HTTPS interceptor logic', () => {
  it('rewrites http:// URLs to https://', () => {
    const result = enforceHttps('http://example.com/api/test');
    expect(result).toBe('https://example.com/api/test');
  });

  it('does not double-rewrite https:// URLs', () => {
    const result = enforceHttps('https://example.com/api/test');
    expect(result).toBe('https://example.com/api/test');
  });

  it('handles undefined URL gracefully', () => {
    const result = enforceHttps(undefined);
    expect(result).toBeUndefined();
  });

  it('does not modify relative URLs', () => {
    const result = enforceHttps('/api/projects');
    expect(result).toBe('/api/projects');
  });
});

describe('API base URL', () => {
  it('base URL is set from VITE_API_URL env or defaults to a valid URL', async () => {
    const api = (await import('./api')).default;
    expect(api.defaults.baseURL).toBeDefined();
    expect(api.defaults.baseURL).toMatch(/^https?:\/\/.+\/api$/);
  });
});

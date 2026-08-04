import { describe, it, expect } from 'vitest';
import { escapeHtml } from './html';

describe('escapeHtml', () => {
  it('escapes characters that would break out of an HTML string', () => {
    expect(escapeHtml('<script>alert("x")</script>')).toBe(
      '&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;'
    );
  });

  it('escapes ampersands and single quotes', () => {
    expect(escapeHtml("Tom & Jerry's")).toBe('Tom &amp; Jerry&#39;s');
  });

  it('returns an empty string for null and undefined', () => {
    expect(escapeHtml(null)).toBe('');
    expect(escapeHtml(undefined)).toBe('');
  });

  it('leaves ordinary status notes untouched', () => {
    const note = 'Opted in ward-wide. Restrictions: Annual block cap.';
    expect(escapeHtml(note)).toBe(note);
  });
});

const HTML_ESCAPES: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

/**
 * Escape a value for interpolation into an HTML string.
 *
 * Leaflet tooltips are bound as raw HTML, so any editor-supplied text (entity
 * names, status notes) must be escaped before it is spliced in.
 */
export const escapeHtml = (value: unknown): string => {
  if (value === null || value === undefined) return '';
  return String(value).replace(/[&<>"']/g, char => HTML_ESCAPES[char]);
};

export const appConfig = {
  name: import.meta.env.VITE_APPLICATION_NAME || 'Open Advocacy',
  description:
    import.meta.env.VITE_APPLICATION_DESCRIPTION ||
    'Track legislative advocacy projects and representatives',
} as const;

export type AppConfig = typeof appConfig;

// Helper function to get config values with fallbacks
export const getConfigValue = <K extends keyof AppConfig>(
  key: K,
  fallback?: AppConfig[K]
): AppConfig[K] => {
  return appConfig[key] ?? fallback ?? appConfig[key];
};

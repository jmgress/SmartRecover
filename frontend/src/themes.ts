export const THEME_STORAGE_KEY = 'theme';

export const themes = [
  { id: 'blue-enterprise', name: 'Blue Enterprise' },
  { id: 'purple', name: 'Purple' },
  { id: 'dark', name: 'Dark' },
  { id: 'high-contrast', name: 'High Contrast' },
  { id: 'green-teal', name: 'Green / Teal' },
] as const;

export type ThemeId = typeof themes[number]['id'];

const isThemeId = (theme: string | null): theme is ThemeId =>
  themes.some(({ id }) => id === theme);

export const getTheme = (): ThemeId => {
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
  return isThemeId(savedTheme) ? savedTheme : 'purple';
};

export const applyTheme = (theme: ThemeId): void => {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_STORAGE_KEY, theme);
};

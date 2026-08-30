export const themes = [
  { id: 'blue-enterprise', name: 'Blue Enterprise', swatch: '#2563eb' },
  { id: 'purple', name: 'Purple', swatch: '#7c3aed' },
  { id: 'dark', name: 'Dark', swatch: '#38bdf8' },
  { id: 'high-contrast', name: 'High Contrast', swatch: '#ffff00' },
  { id: 'green-teal', name: 'Green/Teal', swatch: '#0f766e' },
] as const;

export type Theme = typeof themes[number]['id'];

const THEME_STORAGE_KEY = 'theme';
const defaultTheme = themes.find(({ id }) => id === 'purple')?.id ?? themes[0].id;

export const getTheme = (): Theme => {
  try {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    return themes.some(({ id }) => id === savedTheme) ? savedTheme as Theme : defaultTheme;
  } catch {
    return defaultTheme;
  }
};

export const setTheme = (theme: Theme): void => {
  document.documentElement.dataset.theme = theme;

  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {}
};

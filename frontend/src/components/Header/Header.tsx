import React, { useState, useRef, useEffect } from 'react';
import { FiSettings, FiUser } from 'react-icons/fi';
import { applyTheme, getTheme, themes, ThemeId } from '../../themes';
import styles from './Header.module.css';

const THEME_SWATCHES: Record<ThemeId, string> = {
  'blue-enterprise': '#2563eb',
  purple: '#7c3aed',
  dark: '#111827',
  'high-contrast': '#000000',
  'green-teal': '#0f766e',
};

interface HeaderProps {
  onShowAdmin: () => void;
  showingAdmin: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onShowAdmin, showingAdmin }) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState<ThemeId>(getTheme);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleThemeChange = (theme: ThemeId) => {
    applyTheme(theme);
    setSelectedTheme(theme);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
    };

    if (isProfileOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isProfileOpen]);

  const handleSettingsClick = () => {
    onShowAdmin();
  };

  const handleProfileToggle = () => {
    setIsProfileOpen(!isProfileOpen);
  };

  return (
    <div className={styles.header}>
      <h1 className={styles.appTitle}>SmartRecover</h1>
      <div className={styles.iconContainer}>
        <button
          className={`${styles.iconButton} ${showingAdmin ? styles.active : ''}`}
          onClick={handleSettingsClick}
          title="Settings"
          aria-label="Settings"
        >
          <FiSettings className={styles.icon} size={20} />
        </button>
        
        <div className={styles.profileContainer} ref={dropdownRef}>
          <button
            className={styles.iconButton}
            onClick={handleProfileToggle}
            title="Profile"
            aria-label="Profile menu"
            aria-haspopup="true"
            aria-expanded={isProfileOpen}
          >
            <FiUser className={styles.icon} size={20} />
          </button>
          
          {isProfileOpen && (
            <div className={styles.dropdown} role="menu">
              <div className={styles.themeSection}>
                <span className={styles.themeHeading} id="profile-theme-heading">
                  Theme
                </span>
                <div
                  className={styles.themePicker}
                  role="radiogroup"
                  aria-labelledby="profile-theme-heading"
                >
                  {themes.map((theme) => (
                    <button
                      key={theme.id}
                      type="button"
                      className={`${styles.themeOption} ${selectedTheme === theme.id ? styles.themeOptionActive : ''}`}
                      role="radio"
                      aria-checked={selectedTheme === theme.id}
                      onClick={() => handleThemeChange(theme.id)}
                    >
                      <span
                        className={styles.themeSwatch}
                        style={{ background: THEME_SWATCHES[theme.id] }}
                        aria-hidden="true"
                      />
                      {theme.name}
                    </button>
                  ))}
                </div>
              </div>
              <button
                className={styles.dropdownItem}
                role="menuitem"
                onClick={() => {
                  // TODO: Implement profile settings navigation from dropdown.
                }}
              >
                Settings
              </button>
              <button
                className={styles.dropdownItem}
                role="menuitem"
                onClick={() => {
                  // TODO: Implement logout handling from profile dropdown.
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

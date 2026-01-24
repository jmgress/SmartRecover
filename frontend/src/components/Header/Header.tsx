import React, { useState, useRef, useEffect } from 'react';
import { FiSettings, FiUser } from 'react-icons/fi';
import styles from './Header.module.css';

interface HeaderProps {
  onShowAdmin: () => void;
  showingAdmin: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onShowAdmin, showingAdmin }) => {
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

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

  return (
    <div className={styles.header}>
      <div className={styles.iconContainer}>
        <button
          className={`${styles.iconButton} ${showingAdmin ? styles.active : ''}`}
          onClick={handleSettingsClick}
          title="Settings"
        >
          <FiSettings className={styles.icon} size={20} />
        </button>
        
        <div className={styles.profileContainer} ref={dropdownRef}>
          <button
            className={styles.iconButton}
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            title="Profile"
          >
            <FiUser className={styles.icon} size={20} />
          </button>
          
          {isProfileOpen && (
            <div className={styles.dropdown}>
              <button className={styles.dropdownItem}>
                Settings
              </button>
              <button className={styles.dropdownItem}>
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

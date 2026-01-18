import React from 'react';
import styles from './SeverityBadge.module.css';

interface SeverityBadgeProps {
  severity: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  return (
    <span className={`${styles.severity} ${styles[severity.toLowerCase()]}`}>
      {severity}
    </span>
  );
};

import React from 'react';
import styles from './QualityBadge.module.css';

interface QualityBadgeProps {
  level: 'good' | 'warning' | 'poor';
  score?: number;
  showScore?: boolean;
}

export const QualityBadge: React.FC<QualityBadgeProps> = ({ 
  level, 
  score,
  showScore = false 
}) => {
  const getLabel = () => {
    switch (level) {
      case 'good':
        return 'Good Quality';
      case 'warning':
        return 'Needs Improvement';
      case 'poor':
        return 'Poor Quality';
      default:
        return 'Unknown';
    }
  };

  return (
    <span className={`${styles.quality} ${styles[level]}`}>
      {getLabel()}
      {showScore && score !== undefined && ` (${Math.round(score * 100)}%)`}
    </span>
  );
};

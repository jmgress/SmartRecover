import React from 'react';
import styles from './FilterButtons.module.css';

export type IncidentStatusFilter = 'open' | 'investigating' | 'closed';

interface FilterButtonsProps {
  activeFilter: IncidentStatusFilter;
  onFilterChange: (filter: IncidentStatusFilter) => void;
}

export const FilterButtons: React.FC<FilterButtonsProps> = ({ activeFilter, onFilterChange }) => {
  const filters: { value: IncidentStatusFilter; label: string }[] = [
    { value: 'open', label: 'Open' },
    { value: 'investigating', label: 'Investigating' },
    { value: 'closed', label: 'Closed' },
  ];

  return (
    <div className={styles.filterContainer}>
      <div className={styles.filterButtons}>
        {filters.map((filter) => (
          <button
            key={filter.value}
            className={`${styles.filterButton} ${activeFilter === filter.value ? styles.active : ''}`}
            onClick={() => onFilterChange(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>
    </div>
  );
};

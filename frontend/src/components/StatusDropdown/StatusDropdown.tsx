import React, { useState } from 'react';
import { useUpdateIncidentStatus } from '../../hooks/useUpdateIncidentStatus';
import { Incident } from '../../types/incident';
import styles from './StatusDropdown.module.css';

interface StatusDropdownProps {
  incident: Incident;
  onStatusUpdate?: (updatedIncident: Incident) => void;
}

const STATUS_OPTIONS = [
  { value: 'open', label: 'Open' },
  { value: 'investigating', label: 'Investigating' },
  { value: 'resolved', label: 'Resolved' },
];

export const StatusDropdown: React.FC<StatusDropdownProps> = ({ incident, onStatusUpdate }) => {
  const [optimisticStatus, setOptimisticStatus] = useState<string | null>(null);
  const [showError, setShowError] = useState(false);
  
  const { updateStatus, isUpdating, error } = useUpdateIncidentStatus(
    (updatedIncident) => {
      // Success - clear optimistic state and notify parent
      setOptimisticStatus(null);
      setShowError(false);
      onStatusUpdate?.(updatedIncident);
    },
    () => {
      // Error - show error and revert optimistic update
      setShowError(true);
      setTimeout(() => {
        setOptimisticStatus(null);
        setShowError(false);
      }, 3000);
    }
  );

  const handleStatusChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value;
    
    // Optimistic update
    setOptimisticStatus(newStatus);
    setShowError(false);
    
    try {
      await updateStatus(incident.id, newStatus);
    } catch (err) {
      // Error handling is done in the hook's onError callback
      console.error('Failed to update status:', err);
    }
  };

  const displayStatus = optimisticStatus || incident.status;
  const statusClass = `${styles.statusSelect} ${styles[`status${displayStatus}`]}`;

  return (
    <div className={styles.container}>
      <select
        value={displayStatus}
        onChange={handleStatusChange}
        disabled={isUpdating}
        className={statusClass}
        aria-label="Incident status"
      >
        {STATUS_OPTIONS.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {isUpdating && <span className={styles.updating}>Updating...</span>}
      {showError && error && (
        <span className={styles.error} role="alert">
          {error}
        </span>
      )}
    </div>
  );
};

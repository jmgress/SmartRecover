import React from 'react';
import { Incident } from '../../types/incident';
import { IncidentItem } from '../IncidentItem';
import { FilterButtons, IncidentStatusFilter } from '../FilterButtons';
import styles from './Sidebar.module.css';

interface SidebarProps {
  incidents: Incident[];
  selectedIncidentId: string | null;
  onSelectIncident: (id: string) => void;
  onShowAdmin: () => void;
  showingAdmin: boolean;
  activeFilter: IncidentStatusFilter;
  onFilterChange: (filter: IncidentStatusFilter) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
  onShowAdmin,
  showingAdmin,
  activeFilter,
  onFilterChange,
}) => {
  return (
    <div className={styles.sidebar}>
      <h2 className={styles.title}>Incidents</h2>
      <button
        className={`${styles.adminButton} ${showingAdmin ? styles.active : ''}`}
        onClick={onShowAdmin}
      >
        🔧 Admin
      </button>
      <FilterButtons activeFilter={activeFilter} onFilterChange={onFilterChange} />
      <ul className={styles.incidentList}>
        {incidents.map((incident) => (
          <IncidentItem
            key={incident.id}
            incident={incident}
            isActive={incident.id === selectedIncidentId}
            onClick={() => onSelectIncident(incident.id)}
          />
        ))}
      </ul>
    </div>
  );
};

import React from 'react';
import { Incident } from '../../types/incident';
import { IncidentItem } from '../IncidentItem';
import styles from './Sidebar.module.css';

interface SidebarProps {
  incidents: Incident[];
  selectedIncidentId: string | null;
  onSelectIncident: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  incidents,
  selectedIncidentId,
  onSelectIncident,
}) => {
  return (
    <div className={styles.sidebar}>
      <h2 className={styles.title}>Incidents</h2>
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

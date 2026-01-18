import React from 'react';
import { Incident } from '../../types/incident';
import { SeverityBadge } from '../SeverityBadge';
import styles from './IncidentItem.module.css';

interface IncidentItemProps {
  incident: Incident;
  isActive: boolean;
  onClick: () => void;
}

export const IncidentItem: React.FC<IncidentItemProps> = ({ incident, isActive, onClick }) => {
  return (
    <li
      className={`${styles.incidentItem} ${isActive ? styles.active : ''}`}
      onClick={onClick}
    >
      <h4 className={styles.title}>
        {incident.id}: {incident.title}
      </h4>
      <SeverityBadge severity={incident.severity} />
    </li>
  );
};

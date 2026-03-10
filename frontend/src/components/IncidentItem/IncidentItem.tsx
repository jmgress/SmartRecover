import React from 'react';
import { Incident } from '../../types/incident';
import styles from './IncidentItem.module.css';

interface IncidentItemProps {
  incident: Incident;
  isActive: boolean;
  onClick: () => void;
}

const PRIORITY_LABELS: Record<string, string> = {
  critical: '1 - Critical',
  high: '2 - High',
  medium: '3 - Moderate',
  low: '4 - Low',
};

const STATE_LABELS: Record<string, string> = {
  open: 'New',
  investigating: 'In Progress',
  resolved: 'Resolved',
  closed: 'Closed',
};

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

export const IncidentItem: React.FC<IncidentItemProps> = ({ incident, isActive, onClick }) => {
  const priorityLabel = PRIORITY_LABELS[incident.severity?.toLowerCase()] ?? incident.severity;
  const stateLabel = STATE_LABELS[incident.status?.toLowerCase()] ?? incident.status;

  return (
    <li
      className={`${styles.incidentItem} ${styles[incident.severity?.toLowerCase()]} ${isActive ? styles.active : ''}`}
      onClick={onClick}
    >
      <div className={styles.priorityBar} />
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={styles.incidentNumber}>{incident.id}</span>
          <span className={`${styles.stateBadge} ${styles['state_' + (incident.status?.toLowerCase() ?? '')]}`}>
            {stateLabel}
          </span>
        </div>
        <p className={styles.title}>{incident.title}</p>
        <div className={styles.meta}>
          <span className={`${styles.priorityBadge} ${styles['priority_' + (incident.severity?.toLowerCase() ?? '')]}`}>
            {priorityLabel}
          </span>
        </div>
        <div className={styles.footer}>
          {incident.assignee && (
            <span className={styles.assignee} title="Assigned to">
              <svg className={styles.icon} viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="5" r="3" stroke="currentColor" strokeWidth="1.5" />
                <path d="M2 14c0-3.314 2.686-6 6-6s6 2.686 6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              {incident.assignee}
            </span>
          )}
          <span className={styles.date} title="Opened">
            <svg className={styles.icon} viewBox="0 0 16 16" fill="none">
              <rect x="2" y="3" width="12" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.5" />
              <path d="M5 1v3M11 1v3M2 7h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            {formatDate(incident.created_at)}
          </span>
        </div>
      </div>
    </li>
  );
};

import React from 'react';
import { AgentResults, Incident } from '../../types/incident';
import { buildTimelineEvents } from '../../utils/buildTimelineEvents';
import styles from './IncidentTimeline.module.css';

interface IncidentTimelineProps {
  incident: Incident;
  agentResults: AgentResults | null;
}

const TYPE_LABELS: Record<string, string> = {
  incident_created: 'Incident',
  incident_updated: 'Update',
  change: 'Change',
  event: 'Event',
  resolution: 'Resolution',
};

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
  incident,
  agentResults,
}) => {
  const events = buildTimelineEvents(incident, agentResults);

  if (events.length === 0) {
    return (
      <div className={styles.container}>
        <p className={styles.emptyState}>No timeline events available.</p>
      </div>
    );
  }

  const formatTimestamp = (timestamp: string) => new Date(timestamp).toLocaleString();

  return (
    <div className={styles.container}>
      <ol className={styles.list} aria-label="Incident timeline">
        {events.map((event) => (
          <li
            key={event.id}
            className={styles.item}
            tabIndex={0}
            aria-label={`${TYPE_LABELS[event.type] || event.type}: ${event.title} at ${formatTimestamp(event.timestamp)}`}
          >
            <span
              className={`${styles.marker} ${styles[`marker_${event.type}`] || ''}`}
              aria-hidden="true"
            ></span>
            <div className={styles.itemHeader}>
              <span className={styles.itemTitle}>{event.title}</span>
              <time className={styles.timestamp} dateTime={event.timestamp}>
                {formatTimestamp(event.timestamp)}
              </time>
            </div>
            {event.description && (
              <p className={styles.description}>{event.description}</p>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
};

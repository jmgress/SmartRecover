import React from 'react';
import { TicketDetails } from '../../types/incident';
import { IncidentTimeline } from '../IncidentTimeline';
import styles from './TimelinePanel.module.css';

interface TimelinePanelProps {
  ticketDetails: TicketDetails | null;
}

export const TimelinePanel: React.FC<TimelinePanelProps> = ({ ticketDetails }) => {
  return (
    <div className={styles.timelinePanel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Timeline</h2>
      </div>
      <div className={styles.scrollableContent}>
        {ticketDetails ? (
          <IncidentTimeline
            incident={ticketDetails.incident}
            agentResults={ticketDetails.agent_results}
          />
        ) : (
          <div className={styles.emptyState}>
            <p>Select an incident to view its timeline</p>
          </div>
        )}
      </div>
    </div>
  );
};

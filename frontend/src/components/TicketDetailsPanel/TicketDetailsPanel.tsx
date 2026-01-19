import React, { useState } from 'react';
import { TicketDetails, Incident } from '../../types/incident';
import { AgentResultsTabs } from './AgentResultsTabs';
import { StatusDropdown } from '../StatusDropdown';
import styles from './TicketDetailsPanel.module.css';

interface TicketDetailsPanelProps {
  ticketDetails: TicketDetails | null;
  loading: boolean;
  onIncidentUpdate?: (incident: Incident) => void;
}

export const TicketDetailsPanel: React.FC<TicketDetailsPanelProps> = ({
  ticketDetails,
  loading,
  onIncidentUpdate,
}) => {
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(
    ticketDetails?.incident || null
  );

  React.useEffect(() => {
    if (ticketDetails?.incident) {
      setCurrentIncident(ticketDetails.incident);
    }
  }, [ticketDetails?.incident]);

  const handleStatusUpdate = (updatedIncident: Incident) => {
    setCurrentIncident(updatedIncident);
    onIncidentUpdate?.(updatedIncident);
  };
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.skeleton}></div>
          <div className={styles.skeleton}></div>
          <div className={styles.skeleton}></div>
        </div>
      </div>
    );
  }

  if (!ticketDetails || !currentIncident) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <h2>No Incident Selected</h2>
          <p>Select an incident from the sidebar to view details</p>
        </div>
      </div>
    );
  }

  const { agent_results } = ticketDetails;
  const incident = currentIncident;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getSeverityClass = (severity: string) => {
    return `${styles.severityBadge} ${styles[`severity${severity.toLowerCase()}`]}`;
  };

  return (
    <div className={styles.container}>
      {/* Ticket Header */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h2 className={styles.incidentId}>{incident.id}</h2>
          <div className={styles.badges}>
            <span className={getSeverityClass(incident.severity)}>
              {incident.severity}
            </span>
            <StatusDropdown incident={incident} onStatusUpdate={handleStatusUpdate} />
          </div>
        </div>
        <h3 className={styles.title}>{incident.title}</h3>
      </div>

      {/* Incident Details */}
      <div className={styles.detailsSection}>
        <h4 className={styles.sectionTitle}>Incident Details</h4>
        <div className={styles.detailsGrid}>
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Description:</span>
            <span className={styles.detailValue}>{incident.description}</span>
          </div>
          
          {incident.affected_services && incident.affected_services.length > 0 && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Affected Services:</span>
              <span className={styles.detailValue}>
                {incident.affected_services.join(', ')}
              </span>
            </div>
          )}
          
          {incident.assignee && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Assignee:</span>
              <span className={styles.detailValue}>{incident.assignee}</span>
            </div>
          )}
          
          <div className={styles.detailItem}>
            <span className={styles.detailLabel}>Created:</span>
            <span className={styles.detailValue}>
              {formatDate(incident.created_at)}
            </span>
          </div>
          
          {incident.updated_at && (
            <div className={styles.detailItem}>
              <span className={styles.detailLabel}>Updated:</span>
              <span className={styles.detailValue}>
                {formatDate(incident.updated_at)}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Agent Results */}
      <div className={styles.agentSection}>
        <h4 className={styles.sectionTitle}>Agent Analysis</h4>
        <AgentResultsTabs agentResults={agent_results} />
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { TicketDetails, Incident, ResolutionRecord } from '../../types/incident';
import { api } from '../../services/api';
import { AgentResultsTabs } from './AgentResultsTabs';
import { SuggestedFixCard } from './SuggestedFixCard';
import { ResolutionFeedback } from './ResolutionFeedback';
import { StatusDropdown } from '../StatusDropdown';
import { formatIncidentNumber } from '../../utils/formatIncidentNumber';
import { getIncidentCategory } from '../../utils/incidentCategory';
import styles from './TicketDetailsPanel.module.css';

interface TicketDetailsPanelProps {
  ticketDetails: TicketDetails | null;
  loading: boolean;
  onIncidentUpdate?: (incident: Incident) => void;
  onRetrieve?: () => void;
  retrieving?: boolean;
  retrieveError?: string | null;
  excludedItems?: string[];
  onExcludeItem?: (itemId: string, itemType: string, source: string) => void;
}

export const TicketDetailsPanel: React.FC<TicketDetailsPanelProps> = ({
  ticketDetails,
  loading,
  onIncidentUpdate,
  onRetrieve,
  retrieving = false,
  retrieveError = null,
  excludedItems = [],
  onExcludeItem,
}) => {
  const [currentIncident, setCurrentIncident] = useState<Incident | null>(
    ticketDetails?.incident || null
  );
  const [resolutionRecord, setResolutionRecord] = useState<ResolutionRecord | null>(null);

  React.useEffect(() => {
    if (ticketDetails?.incident) {
      setCurrentIncident(ticketDetails.incident);
    }
  }, [ticketDetails?.incident]);

  const incidentId = currentIncident?.id;
  const incidentStatus = currentIncident?.status;

  React.useEffect(() => {
    let cancelled = false;
    setResolutionRecord(null);
    if (incidentId && incidentStatus === 'resolved') {
      api
        .getResolution(incidentId)
        .then((record) => {
          if (!cancelled) {
            setResolutionRecord(record);
          }
        })
        .catch(() => {
          // Resolution display is best-effort
        });
    }
    return () => {
      cancelled = true;
    };
  }, [incidentId, incidentStatus]);

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
  const category = getIncidentCategory(incident);
  const automationDecision = agent_results?.automation_decision;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getSeverityClass = (severity: string) => {
    return `${styles.severityBadge} ${styles[`severity${severity.toLowerCase()}`]}`;
  };

  return (
    <div className={styles.container}>
      {/* Ticket Header - Fixed */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <h2 className={styles.incidentId}>{formatIncidentNumber(incident.id)}</h2>
          <div className={styles.badges}>
            <span className={getSeverityClass(incident.severity)}>
              {incident.severity}
            </span>
            <span className={styles.categoryBadge}>{category}</span>
            {automationDecision?.automated && (
              <span className={styles.automationBadge}>Auto-remediated</span>
            )}
            <StatusDropdown incident={incident} onStatusUpdate={handleStatusUpdate} />
          </div>
        </div>
        <h3 className={styles.title}>{incident.title}</h3>
      </div>

      {/* Scrollable Content */}
      <div className={styles.scrollableContent}>
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
              <span className={styles.detailLabel}>Category:</span>
              <span className={styles.detailValue}>{category}</span>
            </div>
            
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

        {/* Recorded resolution for resolved incidents */}
        {resolutionRecord && (
          <div className={styles.detailsSection}>
            <h4 className={styles.sectionTitle}>Resolution</h4>
            <div className={styles.detailsGrid}>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Recorded:</span>
                <span className={styles.detailValue}>
                  {formatDate(resolutionRecord.created_at)}
                </span>
              </div>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Quality score:</span>
                <span className={styles.detailValue}>
                  {Math.round(resolutionRecord.grade.score * 100)}%
                </span>
              </div>
              <div className={styles.detailItem}>
                <span className={styles.detailLabel}>Resolution:</span>
                <span className={styles.detailValue}>{resolutionRecord.resolution_text}</span>
              </div>
            </div>
          </div>
        )}

        {/* Suggested Fix - highlighted most likely remediation */}
        {agent_results?.suggested_fix && (
          <div className={styles.agentSection}>
            <SuggestedFixCard
              suggestedFix={agent_results.suggested_fix}
              automationDecision={automationDecision}
            />
          </div>
        )}
        {automationDecision && (
          <div className={`${styles.automationDecision} ${automationDecision.automated ? styles.automationDecisionSuccess : styles.automationDecisionBlocked}`}>
            <strong>{automationDecision.automated ? 'Auto-remediation approved' : 'Automation blocked'}</strong>
            <span>{automationDecision.reason}</span>
          </div>
        )}
        {agent_results && <ResolutionFeedback incidentId={incident.id} />}

        {/* Teams to Involve - derived from tickets, KB, and change correlation */}
        {agent_results?.recommended_teams && agent_results.recommended_teams.length > 0 && (
          <div className={styles.detailsSection}>
            <h4 className={styles.sectionTitle}>Teams to Involve</h4>
            <ul className={styles.teamList}>
              {agent_results.recommended_teams.map((team) => (
                <li key={team.team} className={styles.teamItem}>
                  <span className={styles.teamName}>{team.team}</span>
                  {team.reasons.length > 0 && (
                    <span className={styles.teamReason}>{team.reasons.join('; ')}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Agent Results */}
        <div className={styles.agentSection}>
          <h4 className={styles.sectionTitle}>Agent Analysis</h4>
          <AgentResultsTabs 
            agentResults={agent_results}
            onRetrieve={onRetrieve}
            retrieving={retrieving}
            retrieveError={retrieveError}
            excludedItems={excludedItems}
            onExcludeItem={onExcludeItem}
          />
        </div>
      </div>
    </div>
  );
};

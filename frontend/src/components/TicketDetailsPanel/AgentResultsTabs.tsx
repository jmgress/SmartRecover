import React, { useState } from 'react';
import { AgentResults } from '../../types/incident';
import { LoadingSpinner } from '../LoadingSpinner/LoadingSpinner';
import { QualityBadge } from '../QualityBadge';
import styles from './AgentResultsTabs.module.css';

interface AgentResultsTabsProps {
  agentResults: AgentResults | null;
  onRetrieve?: () => void;
  retrieving?: boolean;
  retrieveError?: string | null;
  excludedItems?: string[];
  onExcludeItem?: (itemId: string, itemType: string, source: string) => void;
}

type TabType = 'servicenow' | 'knowledge' | 'changes' | 'logs' | 'events' | 'remediations';

export const AgentResultsTabs: React.FC<AgentResultsTabsProps> = ({ 
  agentResults, 
  onRetrieve, 
  retrieving = false, 
  retrieveError = null,
  excludedItems = [],
  onExcludeItem,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('servicenow');
  const [executingScript, setExecutingScript] = useState<string | null>(null);

  // Helper to check if an item is excluded
  const isExcluded = (source: string, itemId: string): boolean => {
    return excludedItems.includes(`${source}:${itemId}`);
  };

  // Helper function to format score as percentage
  const formatScore = (score?: number): string => {
    if (score === undefined) return '';
    return `${(score * 100).toFixed(0)}%`;
  };

  if (!agentResults) {
    return (
      <div className={styles.noResults}>
        {retrieving ? (
          <div className={styles.retrievingContainer}>
            <LoadingSpinner />
            <p className={styles.retrievingText}>Retrieving context...</p>
          </div>
        ) : retrieveError ? (
          <div className={styles.errorContainer}>
            <p className={styles.errorMessage}>{retrieveError}</p>
            <button 
              className={styles.retryButton}
              onClick={onRetrieve}
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            <p>No agent analysis available yet.</p>
            <button 
              className={styles.retrieveButton}
              onClick={onRetrieve}
              disabled={!onRetrieve}
            >
              Retrieve Context
            </button>
          </>
        )}
      </div>
    );
  }

  const renderServiceNowTab = () => {
    const data = agentResults.servicenow_results;
    if (!data) {
      return <div className={styles.tabContent}>No ServiceNow data available.</div>;
    }

    // Helper function to get quality info for a specific incident
    const getQualityForIncident = (incidentId: string) => {
      if (!data.quality_assessment?.ticket_qualities) return null;
      return data.quality_assessment.ticket_qualities.find(
        q => q.ticket_id === incidentId
      );
    };

    return (
      <div className={styles.tabContent}>
        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Similar Incidents ({data.similar_incidents?.length || 0})
          </h5>
          {data.similar_incidents && data.similar_incidents.length > 0 ? (
            <ul className={styles.list}>
              {data.similar_incidents.map((incident, idx) => {
                const quality = getQualityForIncident(incident.id);
                const excluded = isExcluded('incident', incident.id);
                if (excluded) return null; // Don't render excluded items
                return (
                  <li key={idx} className={styles.listItem}>
                    <div className={styles.itemHeader}>
                      <span className={styles.itemId}>{incident.id}</span>
                      {quality && (
                        <QualityBadge 
                          level={quality.level}
                          score={quality.score}
                          showScore={true}
                        />
                      )}
                      {incident.similarity_score && (
                        <span className={styles.correlationScore}>
                          Similarity: {formatScore(incident.similarity_score)}
                        </span>
                      )}
                      {incident.severity && (
                        <span className={`${styles.badge} ${styles[`severity${incident.severity.toLowerCase()}`]}`}>
                          {incident.severity}
                        </span>
                      )}
                      {onExcludeItem && (
                        <button
                          className={styles.deleteButton}
                          onClick={() => onExcludeItem(incident.id, 'incident', 'incident')}
                          title="Remove this incident from chat context"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                    <div className={styles.itemTitle}>{incident.title}</div>
                    {incident.description && (
                      <div className={styles.itemContent}>
                        {incident.description}
                      </div>
                    )}
                    {incident.resolution && (
                      <div className={styles.itemResolution}>
                        <strong>Resolution:</strong> {incident.resolution}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className={styles.noData}>No similar incidents found.</p>
          )}
        </div>
      </div>
    );
  };

  const renderKnowledgeTab = () => {
    const data = agentResults.confluence_results;
    if (!data) {
      return <div className={styles.tabContent}>No knowledge base data available.</div>;
    }

    return (
      <div className={styles.tabContent}>
        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Related Documents ({data.documents?.length || 0})
          </h5>
          {data.documents && data.documents.length > 0 ? (
            <ul className={styles.list}>
              {data.documents.map((doc, idx) => {
                const excluded = isExcluded('document', doc.title);
                if (excluded) return null;
                return (
                  <li key={idx} className={styles.listItem}>
                    <div className={styles.itemHeader}>
                      <span className={styles.itemTitle}>{doc.title}</span>
                      {doc.relevance_score && (
                        <span className={styles.correlationScore}>
                          Score: {formatScore(doc.relevance_score)}
                        </span>
                      )}
                      {onExcludeItem && (
                        <button
                          className={styles.deleteButton}
                          onClick={() => onExcludeItem(doc.title, 'document', 'document')}
                          title="Remove this document from chat context"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                    <div className={styles.itemContent}>{doc.content}</div>
                    {doc.tags && doc.tags.length > 0 && (
                      <div className={styles.tags}>
                        {doc.tags.map((tag, tagIdx) => (
                          <span key={tagIdx} className={styles.tag}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className={styles.noData}>No related documents found.</p>
          )}
        </div>
      </div>
    );
  };

  const renderChangesTab = () => {
    const data = agentResults.change_results;
    if (!data) {
      return <div className={styles.tabContent}>No change correlation data available.</div>;
    }

    const renderChangeItem = (change: any, idx: number) => {
      const excluded = isExcluded('change', change.change_id);
      if (excluded) return null;
      return (
        <li key={idx} className={styles.listItem}>
          <div className={styles.itemHeader}>
            <span className={styles.itemId}>{change.change_id}</span>
            <span className={styles.correlationScore}>
              Score: {(change.correlation_score * 100).toFixed(0)}%
            </span>
            {onExcludeItem && (
              <button
                className={styles.deleteButton}
                onClick={() => onExcludeItem(change.change_id, 'change', 'change')}
                title="Remove this change from chat context"
              >
                ✕
              </button>
            )}
          </div>
          <div className={styles.itemTitle}>{change.description}</div>
          <div className={styles.itemMeta}>
            <span>Deployed: {new Date(change.deployed_at).toLocaleString()}</span>
            {change.service && <span> • Service: {change.service}</span>}
          </div>
        </li>
      );
    };

    return (
      <div className={styles.tabContent}>
        {data.top_suspect && !isExcluded('change', data.top_suspect.change_id) && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>🎯 Top Suspect</h5>
            <div className={styles.topSuspect}>
              <div className={styles.itemHeader}>
                <span className={styles.itemId}>{data.top_suspect.change_id}</span>
                <span className={styles.correlationScoreHigh}>
                  Score: {(data.top_suspect.correlation_score * 100).toFixed(0)}%
                </span>
                {onExcludeItem && (
                  <button
                    className={styles.deleteButton}
                    onClick={() => onExcludeItem(data.top_suspect!.change_id, 'change', 'change')}
                    title="Remove this change from chat context"
                  >
                    ✕
                  </button>
                )}
              </div>
              <div className={styles.itemTitle}>{data.top_suspect.description}</div>
              <div className={styles.itemMeta}>
                Deployed: {new Date(data.top_suspect.deployed_at).toLocaleString()}
              </div>
            </div>
          </div>
        )}

        {data.high_correlation_changes && data.high_correlation_changes.length > 0 && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>
              High Correlation Changes ({data.high_correlation_changes.length})
            </h5>
            <ul className={styles.list}>
              {data.high_correlation_changes.map(renderChangeItem)}
            </ul>
          </div>
        )}

        {data.medium_correlation_changes && data.medium_correlation_changes.length > 0 && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>
              Medium Correlation Changes ({data.medium_correlation_changes.length})
            </h5>
            <ul className={styles.list}>
              {data.medium_correlation_changes.map(renderChangeItem)}
            </ul>
          </div>
        )}

        {(!data.high_correlation_changes || data.high_correlation_changes.length === 0) &&
         (!data.medium_correlation_changes || data.medium_correlation_changes.length === 0) &&
         !data.top_suspect && (
          <p className={styles.noData}>No correlated changes found.</p>
        )}
      </div>
    );
  };

  const renderLogsTab = () => {
    const data = agentResults.logs_results;
    if (!data) {
      return <div className={styles.tabContent}>No logs data available.</div>;
    }

    const getLevelClass = (level: string) => {
      switch (level) {
        case 'ERROR':
          return styles.levelError;
        case 'WARN':
          return styles.levelWarn;
        case 'INFO':
          return styles.levelInfo;
        case 'DEBUG':
          return styles.levelDebug;
        default:
          return '';
      }
    };

    const getConfidenceClass = (score?: number) => {
      if (!score) return '';
      if (score >= 0.7) return styles.confidenceHigh;
      if (score >= 0.5) return styles.confidenceMedium;
      return styles.confidenceLow;
    };

    return (
      <div className={styles.tabContent}>
        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Logs Summary
          </h5>
          <div className={styles.logsSummary}>
            <span className={styles.summaryItem}>
              Total: <strong>{data.total_count}</strong>
            </span>
            <span className={styles.summaryItem}>
              Errors: <strong className={styles.levelError}>{data.error_count}</strong>
            </span>
            <span className={styles.summaryItem}>
              Warnings: <strong className={styles.levelWarn}>{data.warning_count}</strong>
            </span>
          </div>
        </div>

        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Log Entries ({data.logs?.length || 0})
          </h5>
          {data.logs && data.logs.length > 0 ? (
            <ul className={styles.list}>
              {data.logs.map((log, idx) => (
                <li key={idx} className={styles.listItem}>
                  <div className={styles.itemHeader}>
                    <span className={`${styles.badge} ${getLevelClass(log.level)}`}>
                      {log.level}
                    </span>
                    {log.confidence_score !== undefined && (
                      <span className={`${styles.badge} ${getConfidenceClass(log.confidence_score)}`}>
                        Confidence: {(log.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                    <span className={styles.itemMeta}>
                      {new Date(log.timestamp).toLocaleString()}
                    </span>
                    <span className={styles.itemMeta}>
                      Service: {log.service}
                    </span>
                  </div>
                  <div className={styles.itemContent}>
                    {log.message}
                  </div>
                  {log.source && (
                    <div className={styles.itemMeta}>
                      Source: {log.source}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.noData}>No log entries found.</p>
          )}
        </div>
      </div>
    );
  };

  const renderEventsTab = () => {
    const data = agentResults.events_results;
    if (!data) {
      return <div className={styles.tabContent}>No real-time events data available.</div>;
    }

    const getSeverityClass = (severity: string) => {
      switch (severity) {
        case 'CRITICAL':
          return styles.severityCritical;
        case 'WARNING':
          return styles.severityWarning;
        case 'INFO':
          return styles.severityInfo;
        default:
          return '';
      }
    };

    const getConfidenceClass = (score?: number) => {
      if (!score) return '';
      if (score >= 0.7) return styles.confidenceHigh;
      if (score >= 0.5) return styles.confidenceMedium;
      return styles.confidenceLow;
    };

    return (
      <div className={styles.tabContent}>
        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Events Summary
          </h5>
          <div className={styles.logsSummary}>
            <span className={styles.summaryItem}>
              Total: <strong>{data.total_count}</strong>
            </span>
            <span className={styles.summaryItem}>
              Critical: <strong className={styles.severityCritical}>{data.critical_count}</strong>
            </span>
            <span className={styles.summaryItem}>
              Warnings: <strong className={styles.severityWarning}>{data.warning_count}</strong>
            </span>
          </div>
        </div>

        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Real-Time Events ({data.events?.length || 0})
          </h5>
          {data.events && data.events.length > 0 ? (
            <ul className={styles.list}>
              {data.events.map((event, idx) => (
                <li key={idx} className={styles.listItem}>
                  <div className={styles.itemHeader}>
                    <span className={styles.itemId}>{event.id}</span>
                    <span className={`${styles.badge} ${getSeverityClass(event.severity)}`}>
                      {event.severity}
                    </span>
                    {event.confidence_score !== undefined && (
                      <span className={`${styles.badge} ${getConfidenceClass(event.confidence_score)}`}>
                        Confidence: {(event.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                    <span className={styles.itemMeta}>
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className={styles.itemTitle}>{event.type}</div>
                  <div className={styles.itemContent}>
                    <strong>Application:</strong> {event.application}
                  </div>
                  <div className={styles.itemContent}>
                    {event.message}
                  </div>
                  {event.details && (
                    <div className={styles.itemContent}>
                      <strong>Details:</strong> {event.details}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.noData}>No real-time events found.</p>
          )}
        </div>
      </div>
    );
  };

  const renderRemediationsTab = () => {
    const data = agentResults.remediation_results;
    if (!data) {
      return <div className={styles.tabContent}>No remediation data available.</div>;
    }

    const getRiskLevelClass = (level: string) => {
      switch (level) {
        case 'high':
          return styles.riskHigh;
        case 'medium':
          return styles.riskMedium;
        case 'low':
          return styles.riskLow;
        default:
          return '';
      }
    };

    const getConfidenceClass = (score?: number) => {
      if (!score) return '';
      if (score >= 0.7) return styles.confidenceHigh;
      if (score >= 0.5) return styles.confidenceMedium;
      return styles.confidenceLow;
    };

    const handleExecuteScript = async (remediationId: string, script: string) => {
      // Set loading state
      setExecutingScript(remediationId);
      
      // Simulate script execution for demo purposes
      console.log(`🚀 Executing script for Remediation ID: ${remediationId}`);
      console.log(`Script:\n${script}`);
      
      try {
        // Simulate execution time (2.5 seconds)
        await new Promise(resolve => setTimeout(resolve, 2500));
        
        // Show success message
        console.log(`✓ Script executed successfully! Remediation ID: ${remediationId}`);
        
        // For demonstration purposes, show alert (in production, use toast notification library)
        alert(`✅ Script Executed Successfully!\n\nRemediation ID: ${remediationId}\n\nThe following script has been simulated:\n${script.substring(0, 100)}${script.length > 100 ? '...' : ''}`);
      } catch (err) {
        console.error('Failed to execute script:', err);
        alert('Failed to execute script');
      } finally {
        // Clear loading state
        setExecutingScript(null);
      }
    };

    return (
      <div className={styles.tabContent}>
        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Recommended Remediations ({data.remediations?.length || 0})
          </h5>
          {data.remediations && data.remediations.length > 0 ? (
            <ul className={styles.list}>
              {data.remediations.map((remediation, idx) => (
                <li key={idx} className={styles.listItem}>
                  <div className={styles.itemHeader}>
                    <span className={styles.itemTitle}>{remediation.title}</span>
                    <span className={`${styles.badge} ${getRiskLevelClass(remediation.risk_level)}`}>
                      {remediation.risk_level.toUpperCase()} RISK
                    </span>
                    {remediation.confidence_score !== undefined && (
                      <span className={`${styles.badge} ${getConfidenceClass(remediation.confidence_score)}`}>
                        Confidence: {(remediation.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <div className={styles.itemContent}>
                    {remediation.description}
                  </div>
                  <div className={styles.remediationMeta}>
                    <span><strong>Duration:</strong> {remediation.estimated_duration}</span>
                  </div>
                  {remediation.prerequisites && remediation.prerequisites.length > 0 && (
                    <div className={styles.prerequisites}>
                      <strong>Prerequisites:</strong>
                      <ul className={styles.prerequisiteList}>
                        {remediation.prerequisites.map((prereq, prereqIdx) => (
                          <li key={prereqIdx}>{prereq}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className={styles.scriptContainer}>
                    <strong>Script:</strong>
                    <pre className={styles.scriptCode}>{remediation.script}</pre>
                    <button 
                      className={styles.executeButton}
                      onClick={() => handleExecuteScript(remediation.id, remediation.script)}
                      disabled={executingScript === remediation.id}
                    >
                      {executingScript === remediation.id ? '⏳ Running...' : '▶️ Run Script'}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.noData}>No remediation recommendations found.</p>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'servicenow' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('servicenow')}
        >
          Prior Incidents
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'knowledge' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('knowledge')}
        >
          Knowledge Base
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'changes' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('changes')}
        >
          Change Correlation
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'logs' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          Logs
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'events' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('events')}
        >
          Real-Time Events
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'remediations' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('remediations')}
        >
          Remediations
        </button>
      </div>

      {activeTab === 'servicenow' && renderServiceNowTab()}
      {activeTab === 'knowledge' && renderKnowledgeTab()}
      {activeTab === 'changes' && renderChangesTab()}
      {activeTab === 'logs' && renderLogsTab()}
      {activeTab === 'events' && renderEventsTab()}
      {activeTab === 'remediations' && renderRemediationsTab()}
    </div>
  );
};

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
}

type TabType = 'servicenow' | 'knowledge' | 'changes';

export const AgentResultsTabs: React.FC<AgentResultsTabsProps> = ({ 
  agentResults, 
  onRetrieve, 
  retrieving = false, 
  retrieveError = null 
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('servicenow');

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

    return (
      <div className={styles.tabContent}>
        {/* Quality Assessment Section */}
        {data.quality_assessment && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>
              Data Quality Assessment
            </h5>
            <div className={styles.qualitySection}>
              <QualityBadge 
                level={data.quality_assessment.overall_level}
                score={data.quality_assessment.average_score}
                showScore={true}
              />
              <div className={styles.qualitySummary}>
                <span className={styles.qualityDetail}>
                  {data.quality_assessment.summary.good_count} good, {' '}
                  {data.quality_assessment.summary.warning_count} need improvement, {' '}
                  {data.quality_assessment.summary.poor_count} poor
                </span>
              </div>
            </div>
          </div>
        )}

        <div className={styles.section}>
          <h5 className={styles.subsectionTitle}>
            Similar Incidents ({data.similar_incidents?.length || 0})
          </h5>
          {data.similar_incidents && data.similar_incidents.length > 0 ? (
            <ul className={styles.list}>
              {data.similar_incidents.map((incident, idx) => (
                <li key={idx} className={styles.listItem}>
                  <div className={styles.itemHeader}>
                    <span className={styles.itemId}>{incident.id}</span>
                    {incident.severity && (
                      <span className={`${styles.badge} ${styles[`severity${incident.severity.toLowerCase()}`]}`}>
                        {incident.severity}
                      </span>
                    )}
                  </div>
                  <div className={styles.itemTitle}>{incident.title}</div>
                  {incident.resolution && (
                    <div className={styles.itemResolution}>
                      <strong>Resolution:</strong> {incident.resolution}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className={styles.noData}>No similar incidents found.</p>
          )}
        </div>

        {data.resolutions && data.resolutions.length > 0 && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>Previous Resolutions</h5>
            <ul className={styles.list}>
              {data.resolutions.map((resolution, idx) => (
                <li key={idx} className={styles.listItem}>
                  {resolution}
                </li>
              ))}
            </ul>
          </div>
        )}
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
              {data.documents.map((doc, idx) => (
                <li key={idx} className={styles.listItem}>
                  <div className={styles.itemTitle}>{doc.title}</div>
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
              ))}
            </ul>
          ) : (
            <p className={styles.noData}>No related documents found.</p>
          )}
        </div>

        {data.content_summaries && data.content_summaries.length > 0 && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>Content Summaries</h5>
            <ul className={styles.list}>
              {data.content_summaries.map((summary, idx) => (
                <li key={idx} className={styles.listItem}>
                  {summary}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderChangesTab = () => {
    const data = agentResults.change_results;
    if (!data) {
      return <div className={styles.tabContent}>No change correlation data available.</div>;
    }

    const renderChangeItem = (change: any, idx: number) => (
      <li key={idx} className={styles.listItem}>
        <div className={styles.itemHeader}>
          <span className={styles.itemId}>{change.change_id}</span>
          <span className={styles.correlationScore}>
            Score: {(change.correlation_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className={styles.itemTitle}>{change.description}</div>
        <div className={styles.itemMeta}>
          <span>Deployed: {new Date(change.deployed_at).toLocaleString()}</span>
          {change.service && <span> • Service: {change.service}</span>}
        </div>
      </li>
    );

    return (
      <div className={styles.tabContent}>
        {data.top_suspect && (
          <div className={styles.section}>
            <h5 className={styles.subsectionTitle}>🎯 Top Suspect</h5>
            <div className={styles.topSuspect}>
              <div className={styles.itemHeader}>
                <span className={styles.itemId}>{data.top_suspect.change_id}</span>
                <span className={styles.correlationScoreHigh}>
                  {(data.top_suspect.correlation_score * 100).toFixed(0)}%
                </span>
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

  return (
    <div className={styles.container}>
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'servicenow' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('servicenow')}
        >
          ServiceNow
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
          Changes
        </button>
      </div>

      {activeTab === 'servicenow' && renderServiceNowTab()}
      {activeTab === 'knowledge' && renderKnowledgeTab()}
      {activeTab === 'changes' && renderChangesTab()}
    </div>
  );
};

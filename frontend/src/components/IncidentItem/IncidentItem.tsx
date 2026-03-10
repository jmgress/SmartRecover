import React, { useState, useRef, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { Incident } from '../../types/incident';
import { SeverityBadge } from '../SeverityBadge';
import styles from './IncidentItem.module.css';

interface IncidentItemProps {
  incident: Incident;
  isActive: boolean;
  onClick: () => void;
}

/**
 * Approximate max height of the tooltip in pixels, used to clamp its
 * vertical position so it doesn't overflow the viewport bottom.
 * Update this value if the tooltip content grows significantly.
 */
const TOOLTIP_APPROX_HEIGHT = 280;

/** Category keyword config: each entry maps a display name to title keywords */
const CATEGORY_RULES: Array<{ name: string; keywords: string[] }> = [
  { name: 'Database',       keywords: ['database', 'replica lag', 'connection timeout'] },
  { name: 'Application',    keywords: ['memory leak'] },
  { name: 'Infrastructure', keywords: ['kubernetes', 'container', 'load balancer', 'service mesh'] },
  { name: 'Network',        keywords: ['network', 'latency'] },
  { name: 'Security',       keywords: ['ssl', 'certificate', 'oauth'] },
  { name: 'Storage',        keywords: ['disk', 'storage'] },
  { name: 'Monitoring',     keywords: ['log', 'elasticsearch'] },
  { name: 'Cache',          keywords: ['cache', 'redis', 'cdn'] },
  { name: 'Payments',       keywords: ['payment'] },
  { name: 'API',            keywords: ['api'] },
];

/** Format incident ID to ServiceNow-style 7-digit number (e.g., INC001 → INC0000001) */
function formatIncidentNumber(id: string): string {
  const match = id.match(/^([A-Z]+)(\d+)$/);
  if (match) {
    return `${match[1]}${match[2].padStart(7, '0')}`;
  }
  return id;
}

/** Map severity to ServiceNow priority label */
function getPriority(severity: string): { label: string; cssClass: string } {
  switch (severity.toLowerCase()) {
    case 'critical': return { label: 'P1 - Critical', cssClass: styles.priorityCritical };
    case 'high':     return { label: 'P2 - High',     cssClass: styles.priorityHigh };
    case 'medium':   return { label: 'P3 - Moderate', cssClass: styles.priorityMedium };
    case 'low':      return { label: 'P4 - Low',      cssClass: styles.priorityLow };
    default:         return { label: 'P3 - Moderate', cssClass: styles.priorityMedium };
  }
}

/** Derive a ServiceNow-style category from the incident title */
function getCategory(title: string): string {
  const t = title.toLowerCase();
  for (const rule of CATEGORY_RULES) {
    if (rule.keywords.some(kw => t.includes(kw))) {
      return rule.name;
    }
  }
  return 'Application';
}

/** Format relative time string (e.g., "3h ago", "2d ago") */
function getTimeAgo(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${Math.floor(diffHours / 24)}d ago`;
}

/** Return the singular or plural form of a word based on count */
function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural;
}

/** Map status to CSS class name */
function statusClass(status: string): string {
  switch (status.toLowerCase()) {
    case 'open':          return styles.statusOpen;
    case 'investigating': return styles.statusInvestigating;
    case 'resolved':      return styles.statusResolved;
    default:              return styles.statusOpen;
  }
}

export const IncidentItem: React.FC<IncidentItemProps> = ({ incident, isActive, onClick }) => {
  const [tooltipPos, setTooltipPos] = useState<{ top: number; left: number } | null>(null);
  const itemRef = useRef<HTMLLIElement>(null);

  const handleMouseEnter = useCallback(() => {
    if (itemRef.current) {
      const rect = itemRef.current.getBoundingClientRect();
      const top = Math.min(rect.top, window.innerHeight - TOOLTIP_APPROX_HEIGHT - 8);
      setTooltipPos({ top, left: rect.right + 10 });
    }
  }, []);

  const handleMouseLeave = useCallback(() => {
    setTooltipPos(null);
  }, []);

  const priority = getPriority(incident.severity);
  const category = getCategory(incident.title);
  const formattedId = formatIncidentNumber(incident.id);
  const timeAgo = getTimeAgo(incident.created_at);
  const statusLabel = incident.status.charAt(0).toUpperCase() + incident.status.slice(1);
  const serviceCount = incident.affected_services.length;

  return (
    <li
      ref={itemRef}
      className={`${styles.incidentItem} ${isActive ? styles.active : ''}`}
      onClick={onClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Header row: ServiceNow number + status badge */}
      <div className={styles.incidentHeader}>
        <span className={styles.incidentNumber}>{formattedId}</span>
        <span className={`${styles.statusBadge} ${statusClass(incident.status)}`}>
          {statusLabel}
        </span>
      </div>

      {/* Incident title */}
      <h4 className={styles.title}>{incident.title}</h4>

      {/* Priority + severity row */}
      <div className={styles.metaRow}>
        <span className={`${styles.priorityBadge} ${priority.cssClass}`}>{priority.label}</span>
        <SeverityBadge severity={incident.severity} />
      </div>

      {/* Category + age row */}
      <div className={styles.detailsRow}>
        <span className={styles.category}>{category}</span>
        <span className={styles.timeAgo}>{timeAgo}</span>
      </div>

      {/* Assignee */}
      {incident.assignee && (
        <div className={styles.assigneeRow}>
          <span className={styles.assigneeLabel}>Assigned to:</span>
          <span className={styles.assigneeValue}>{incident.assignee}</span>
        </div>
      )}

      {/* Affected services count */}
      <div className={styles.servicesRow}>
        <span className={styles.servicesLabel}>
          {serviceCount} {pluralize(serviceCount, 'service')} affected
        </span>
      </div>

      {/* Hover tooltip – rendered in a portal so it escapes sidebar overflow clipping */}
      {tooltipPos && ReactDOM.createPortal(
        <div
          className={styles.tooltip}
          style={{ top: tooltipPos.top, left: tooltipPos.left }}
        >
          <div className={styles.tooltipHeader}>
            <strong className={styles.tooltipNumber}>{formattedId}</strong>
            <span className={`${styles.statusBadge} ${statusClass(incident.status)}`}>{statusLabel}</span>
          </div>

          <p className={styles.tooltipDescription}>{incident.description}</p>

          <div className={styles.tooltipField}>
            <span className={styles.tooltipLabel}>Priority:</span>
            <span>{priority.label}</span>
          </div>
          <div className={styles.tooltipField}>
            <span className={styles.tooltipLabel}>Category:</span>
            <span>{category}</span>
          </div>
          <div className={styles.tooltipField}>
            <span className={styles.tooltipLabel}>Assigned to:</span>
            <span>{incident.assignee || 'Unassigned'}</span>
          </div>
          <div className={styles.tooltipField}>
            <span className={styles.tooltipLabel}>Opened:</span>
            <span>{new Date(incident.created_at).toLocaleString()}</span>
          </div>
          {incident.updated_at && (
            <div className={styles.tooltipField}>
              <span className={styles.tooltipLabel}>Updated:</span>
              <span>{new Date(incident.updated_at).toLocaleString()}</span>
            </div>
          )}
          <div className={styles.tooltipField}>
            <span className={styles.tooltipLabel}>Services:</span>
            <div className={styles.tooltipServices}>
              {incident.affected_services.map(svc => (
                <span key={svc} className={styles.serviceTag}>{svc}</span>
              ))}
            </div>
          </div>
        </div>,
        document.body
      )}
    </li>
  );
};

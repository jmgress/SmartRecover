import { AgentResults, Incident, TimelineEvent } from '../types/incident';

/**
 * Derives a chronologically ordered list of timeline events from an incident
 * and its agent results (correlated changes, notable events, and the top
 * suggested/remediation resolution).
 */
export function buildTimelineEvents(
  incident: Incident,
  agentResults: AgentResults | null
): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  events.push({
    id: `${incident.id}-created`,
    timestamp: incident.created_at,
    type: 'incident_created',
    title: 'Incident created',
    description: incident.title,
  });

  if (incident.updated_at) {
    events.push({
      id: `${incident.id}-updated`,
      timestamp: incident.updated_at,
      type: 'incident_updated',
      title: `Status updated to ${incident.status}`,
    });
  }

  agentResults?.change_results?.all_correlations?.forEach((change) => {
    events.push({
      id: `change-${change.change_id}`,
      timestamp: change.deployed_at,
      type: 'change',
      title: `Change deployed: ${change.change_id}`,
      description: change.description,
    });
  });

  agentResults?.events_results?.events?.forEach((event) => {
    events.push({
      id: `event-${event.id}`,
      timestamp: event.timestamp,
      type: 'event',
      title: event.type,
      description: event.message,
    });
  });

  const resolution = agentResults?.suggested_fix;
  if (resolution) {
    // SuggestedFix has no timestamp of its own; approximate it as occurring
    // at the incident's last update (falling back to creation time).
    events.push({
      id: `resolution-${resolution.id}`,
      timestamp: incident.updated_at || incident.created_at,
      type: 'resolution',
      title: `Suggested fix: ${resolution.title}`,
      description: resolution.rationale,
    });
  }

  return events.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
}

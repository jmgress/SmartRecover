export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
  updated_at?: string;
  affected_services: string[];
  assignee?: string;
}

export interface IncidentQuery {
  incident_id: string;
  user_query: string;
}

export interface AgentResponse {
  incident_id: string;
  resolution_steps: string[];
  related_knowledge: string[];
  correlated_changes: string[];
  summary: string;
  confidence: number;
}

export interface LLMTestResponse {
  status: string;
  llm_response: string;
  error?: string;
}

export interface LLMConfigResponse {
  provider: string;
  model: string;
  connection_details: {
    api_key_configured?: boolean;
    endpoint?: string;
    base_url?: string;
    local?: boolean;
  };
  temperature: number;
}

export interface LoggingConfigResponse {
  level: string;
  enable_tracing: boolean;
  log_file?: string;
}

export interface UpdateLoggingConfigRequest {
  level?: string;
  enable_tracing?: boolean;
}

// Agent result types for the middle panel
export interface SimilarIncident {
  id: string;
  title: string;
  description?: string;
  resolution?: string;
  severity?: string;
  status?: string;
  similarity_score?: number;
}

export interface QualityAssessment {
  average_score: number;
  overall_level: 'good' | 'warning' | 'poor';
  ticket_qualities: {
    ticket_id: string;
    ticket_type: string;
    score: number;
    level: 'good' | 'warning' | 'poor';
    issues: string[];
    details: {
      description_score?: number;
      resolution_score?: number;
    };
  }[];
  summary: {
    total_tickets: number;
    good_count: number;
    warning_count: number;
    poor_count: number;
  };
}

export interface ServiceNowResult {
  source: string;
  incident_id: string;
  similar_incidents: SimilarIncident[];
  related_changes: any[];
  resolutions: string[];
  quality_assessment?: QualityAssessment;
}

export interface KnowledgeDocument {
  title: string;
  content: string;
  url?: string;
  tags?: string[];
  relevance_score?: number;
}

export interface KnowledgeBaseResult {
  source: string;
  incident_id: string;
  documents: KnowledgeDocument[];
  knowledge_base_articles: string[];
}

export interface CorrelatedChange {
  change_id: string;
  description: string;
  deployed_at: string;
  correlation_score: number;
  service?: string;
}

export interface ChangeCorrelationResult {
  source: string;
  incident_id: string;
  high_correlation_changes: CorrelatedChange[];
  medium_correlation_changes: CorrelatedChange[];
  all_correlations: CorrelatedChange[];
  top_suspect: CorrelatedChange | null;
}

export interface LogEntry {
  timestamp: string;
  level: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  service: string;
  message: string;
  source?: string;
  confidence_score?: number;
}

export interface LogsResult {
  source: string;
  incident_id: string;
  logs: LogEntry[];
  total_count: number;
  error_count: number;
  warning_count: number;
}

export interface Event {
  id: string;
  timestamp: string;
  type: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  application: string;
  message: string;
  details?: string;
  confidence_score?: number;
}

export interface EventsResult {
  source: string;
  incident_id: string;
  events: Event[];
  total_count: number;
  critical_count: number;
  warning_count: number;
}

export interface AgentResults {
  servicenow_results?: ServiceNowResult;
  confluence_results?: KnowledgeBaseResult;
  change_results?: ChangeCorrelationResult;
  logs_results?: LogsResult;
  events_results?: EventsResult;
}

export interface TicketDetails {
  incident: Incident;
  agent_results: AgentResults | null;
}

export interface ChatMessage {
  content: string;
  role: 'user' | 'assistant';
}

export interface AgentPromptInfo {
  current: string;
  default: string;
  is_custom: boolean;
}

export interface AgentPromptsResponse {
  prompts: {
    [agent_name: string]: AgentPromptInfo;
  };
}

export interface UpdateAgentPromptRequest {
  prompt: string;
}

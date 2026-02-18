import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { LLMTestResponse, LLMConfigResponse, LoggingConfigResponse, AgentPromptsResponse, AccuracyMetricsResponse, PromptLogsResponse, PromptLog } from '../types/incident';
import './Admin.css';

type AdminSection = 'llm' | 'logging' | 'prompts' | 'accuracy' | 'prompt-logs';

export const Admin: React.FC = () => {
  // Active tab state
  const [activeSection, setActiveSection] = useState<AdminSection>('llm');
  
  const [testMessage, setTestMessage] = useState('Hello, are you working correctly?');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<LLMTestResponse | null>(null);
  const [llmConfig, setLlmConfig] = useState<LLMConfigResponse | null>(null);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);
  
  // Logging configuration state
  const [loggingConfig, setLoggingConfig] = useState<LoggingConfigResponse | null>(null);
  const [loadingLoggingConfig, setLoadingLoggingConfig] = useState(true);
  const [loggingConfigError, setLoggingConfigError] = useState<string | null>(null);
  const [selectedLogLevel, setSelectedLogLevel] = useState('INFO');
  const [enableTracing, setEnableTracing] = useState(false);
  const [updatingLogging, setUpdatingLogging] = useState(false);
  const [loggingUpdateSuccess, setLoggingUpdateSuccess] = useState<string | null>(null);

  // Agent prompts state
  const [agentPrompts, setAgentPrompts] = useState<AgentPromptsResponse | null>(null);
  const [loadingPrompts, setLoadingPrompts] = useState(true);
  const [promptsError, setPromptsError] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string>('orchestrator');
  const [editedPrompt, setEditedPrompt] = useState<string>('');
  const [updatingPrompt, setUpdatingPrompt] = useState(false);
  const [promptUpdateSuccess, setPromptUpdateSuccess] = useState<string | null>(null);
  const [resettingPrompts, setResettingPrompts] = useState(false);

  // Accuracy metrics state
  const [accuracyMetrics, setAccuracyMetrics] = useState<AccuracyMetricsResponse | null>(null);
  const [loadingAccuracy, setLoadingAccuracy] = useState(true);
  const [accuracyError, setAccuracyError] = useState<string | null>(null);

  // Prompt logs state
  const [promptLogs, setPromptLogs] = useState<PromptLogsResponse | null>(null);
  const [loadingPromptLogs, setLoadingPromptLogs] = useState(true);
  const [promptLogsError, setPromptLogsError] = useState<string | null>(null);
  const [selectedPromptLog, setSelectedPromptLog] = useState<PromptLog | null>(null);
  const [promptLogFilter, setPromptLogFilter] = useState<string>('');

  useEffect(() => {
    fetchLLMConfig();
    fetchLoggingConfig();
    fetchAgentPrompts();
    fetchAccuracyMetrics();
    fetchPromptLogs();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchLLMConfig = async () => {
    setLoadingConfig(true);
    setConfigError(null);
    try {
      const config = await api.getLLMConfig();
      setLlmConfig(config);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load LLM configuration';
      setConfigError(errorMessage);
    } finally {
      setLoadingConfig(false);
    }
  };

  const fetchLoggingConfig = async () => {
    setLoadingLoggingConfig(true);
    setLoggingConfigError(null);
    try {
      const config = await api.getLoggingConfig();
      setLoggingConfig(config);
      setSelectedLogLevel(config.level);
      setEnableTracing(config.enable_tracing);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load logging configuration';
      setLoggingConfigError(errorMessage);
    } finally {
      setLoadingLoggingConfig(false);
    }
  };

  const handleUpdateLogging = async () => {
    setUpdatingLogging(true);
    setLoggingUpdateSuccess(null);
    setLoggingConfigError(null);

    try {
      const updatedConfig = await api.updateLoggingConfig({
        level: selectedLogLevel,
        enable_tracing: enableTracing,
      });
      setLoggingConfig(updatedConfig);
      setLoggingUpdateSuccess('Logging configuration updated successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setLoggingUpdateSuccess(null), 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update logging configuration';
      setLoggingConfigError(errorMessage);
    } finally {
      setUpdatingLogging(false);
    }
  };

  const fetchAgentPrompts = async () => {
    setLoadingPrompts(true);
    setPromptsError(null);
    try {
      const prompts = await api.getAgentPrompts();
      setAgentPrompts(prompts);
      // Set initial edited prompt
      if (prompts.prompts[selectedAgent]) {
        setEditedPrompt(prompts.prompts[selectedAgent].current);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load agent prompts';
      setPromptsError(errorMessage);
    } finally {
      setLoadingPrompts(false);
    }
  };

  const handleAgentChange = (agent: string) => {
    setSelectedAgent(agent);
    if (agentPrompts?.prompts[agent]) {
      setEditedPrompt(agentPrompts.prompts[agent].current);
    }
    setPromptUpdateSuccess(null);
  };

  const handleUpdatePrompt = async () => {
    setUpdatingPrompt(true);
    setPromptUpdateSuccess(null);
    setPromptsError(null);

    try {
      const updatedPrompt = await api.updateAgentPrompt(selectedAgent, editedPrompt);
      
      // Update local state
      if (agentPrompts) {
        setAgentPrompts({
          prompts: {
            ...agentPrompts.prompts,
            [selectedAgent]: updatedPrompt
          }
        });
      }
      
      setPromptUpdateSuccess(`Prompt updated successfully for ${selectedAgent}!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setPromptUpdateSuccess(null), 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update agent prompt';
      setPromptsError(errorMessage);
    } finally {
      setUpdatingPrompt(false);
    }
  };

  const handleResetPrompt = async () => {
    if (!window.confirm(`Are you sure you want to reset the ${selectedAgent} prompt to its default value?`)) {
      return;
    }

    setResettingPrompts(true);
    setPromptUpdateSuccess(null);
    setPromptsError(null);

    try {
      await api.resetAgentPrompts(selectedAgent);
      
      // Refresh prompts
      await fetchAgentPrompts();
      
      setPromptUpdateSuccess(`Prompt reset successfully for ${selectedAgent}!`);
      
      // Clear success message after 3 seconds
      setTimeout(() => setPromptUpdateSuccess(null), 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reset agent prompt';
      setPromptsError(errorMessage);
    } finally {
      setResettingPrompts(false);
    }
  };

  const handleResetAllPrompts = async () => {
    if (!window.confirm('Are you sure you want to reset ALL agent prompts to their default values?')) {
      return;
    }

    setResettingPrompts(true);
    setPromptUpdateSuccess(null);
    setPromptsError(null);

    try {
      await api.resetAgentPrompts();
      
      // Refresh prompts
      await fetchAgentPrompts();
      
      setPromptUpdateSuccess('All prompts reset successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setPromptUpdateSuccess(null), 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to reset all prompts';
      setPromptsError(errorMessage);
    } finally {
      setResettingPrompts(false);
    }
  };

  const fetchAccuracyMetrics = async () => {
    setLoadingAccuracy(true);
    setAccuracyError(null);
    try {
      const metrics = await api.getAccuracyMetrics();
      setAccuracyMetrics(metrics);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load accuracy metrics';
      setAccuracyError(errorMessage);
    } finally {
      setLoadingAccuracy(false);
    }
  };

  const fetchPromptLogs = async () => {
    setLoadingPromptLogs(true);
    setPromptLogsError(null);
    try {
      const logs = await api.getPromptLogs();
      setPromptLogs(logs);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load prompt logs';
      setPromptLogsError(errorMessage);
    } finally {
      setLoadingPromptLogs(false);
    }
  };

  const handleClearPromptLogs = async () => {
    if (!window.confirm('Are you sure you want to clear all prompt logs?')) {
      return;
    }
    
    try {
      await api.clearPromptLogs();
      await fetchPromptLogs();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to clear prompt logs';
      setPromptLogsError(errorMessage);
    }
  };

  const handleTestLLM = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      const result = await api.testLLM(testMessage);
      setTestResult(result);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred';
      setTestResult({
        status: 'error',
        llm_response: '',
        error: errorMessage,
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="admin-container">
      <h1>Admin - System Configuration</h1>
      
      {/* Tab Navigation */}
      <div className="admin-tabs">
        <button 
          className={`admin-tab ${activeSection === 'llm' ? 'active' : ''}`}
          onClick={() => setActiveSection('llm')}
        >
          Test LLM
        </button>
        <button 
          className={`admin-tab ${activeSection === 'logging' ? 'active' : ''}`}
          onClick={() => setActiveSection('logging')}
        >
          Logging & Tracing
        </button>
        <button 
          className={`admin-tab ${activeSection === 'prompts' ? 'active' : ''}`}
          onClick={() => setActiveSection('prompts')}
        >
          Agent Prompts
        </button>
        <button 
          className={`admin-tab ${activeSection === 'accuracy' ? 'active' : ''}`}
          onClick={() => setActiveSection('accuracy')}
        >
          Accuracy Metrics
        </button>
        <button 
          className={`admin-tab ${activeSection === 'prompt-logs' ? 'active' : ''}`}
          onClick={() => setActiveSection('prompt-logs')}
        >
          Prompt Logs
        </button>
      </div>

      {/* LLM Testing Section */}
      {activeSection === 'llm' && (
        <>
          <div className="config-section">
            <h2>Current LLM Configuration</h2>
            {loadingConfig ? (
              <p className="loading-text">Loading configuration...</p>
            ) : configError ? (
              <div className="config-error">
                <p><strong>Error:</strong> {configError}</p>
              </div>
            ) : llmConfig ? (
              <div className="config-details">
                <div className="config-item">
                  <span className="config-label">Provider:</span>
                  <span className="config-value provider-badge">{llmConfig.provider.toUpperCase()}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">Model:</span>
                  <span className="config-value">{llmConfig.model}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">Temperature:</span>
                  <span className="config-value">{llmConfig.temperature}</span>
                </div>
                {llmConfig.provider === 'ollama' && llmConfig.connection_details.base_url && (
                  <div className="config-item">
                    <span className="config-label">Base URL:</span>
                    <span className="config-value">{llmConfig.connection_details.base_url}</span>
                  </div>
                )}
                {llmConfig.provider === 'ollama' && llmConfig.connection_details.local && (
                  <div className="config-item">
                    <span className="config-label">Type:</span>
                    <span className="config-value">Local (No API key required)</span>
                  </div>
                )}
                {(llmConfig.provider === 'openai' || llmConfig.provider === 'gemini') && (
                  <>
                    <div className="config-item">
                      <span className="config-label">Endpoint:</span>
                      <span className="config-value">{llmConfig.connection_details.endpoint}</span>
                    </div>
                    <div className="config-item">
                      <span className="config-label">API Key:</span>
                      <span className={`config-value ${llmConfig.connection_details.api_key_configured ? 'status-ok' : 'status-error'}`}>
                        {llmConfig.connection_details.api_key_configured ? '✓ Configured' : '✗ Not configured'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            ) : null}
          </div>
          
          <div className="test-section">
            <h2>Test LLM Connection</h2>
            <p>Send a test message to verify the AI system is communicating correctly.</p>
            
            <div className="input-group">
              <label htmlFor="testMessage">Test Message:</label>
              <input
                id="testMessage"
                type="text"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Enter a test message..."
                disabled={testing}
              />
            </div>

            <button 
              className="test-button"
              onClick={handleTestLLM}
              disabled={testing || !testMessage.trim()}
            >
              {testing ? 'Testing...' : 'Test LLM'}
            </button>

            {testResult && (
              <div className={`test-result ${testResult.status}`}>
                <h3>Test Result</h3>
                
                <div className="result-item">
                  <strong>Status:</strong> 
                  <span className={`status-badge ${testResult.status}`}>
                    {testResult.status}
                  </span>
                </div>

                {testResult.status === 'success' && testResult.llm_response && (
                  <div className="result-item llm-response">
                    <strong>LLM Response:</strong>
                    <div className="response-content">{testResult.llm_response}</div>
                  </div>
                )}

                {testResult.error && (
                  <div className="result-item error-message">
                    <strong>Error:</strong>
                    <div className="error-content">{testResult.error}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      {/* Logging Configuration Section */}
      {activeSection === 'logging' && (
        <div className="config-section">
          <h2>Logging Configuration</h2>
          {loadingLoggingConfig ? (
            <p className="loading-text">Loading logging configuration...</p>
          ) : loggingConfigError ? (
            <div className="config-error">
              <p><strong>Error:</strong> {loggingConfigError}</p>
            </div>
          ) : loggingConfig ? (
            <div className="logging-controls">
              <div className="config-details">
                <div className="config-item">
                  <span className="config-label">Current Level:</span>
                  <span className="config-value">{loggingConfig.level}</span>
                </div>
                <div className="config-item">
                  <span className="config-label">Tracing Enabled:</span>
                  <span className="config-value">{loggingConfig.enable_tracing ? 'Yes' : 'No'}</span>
                </div>
                {loggingConfig.log_file && (
                  <div className="config-item">
                    <span className="config-label">Log File:</span>
                    <span className="config-value">{loggingConfig.log_file}</span>
                  </div>
                )}
              </div>

              <div className="logging-update-section">
                <h3>Update Logging Settings</h3>
                
                <div className="input-group">
                  <label htmlFor="logLevel">Log Level:</label>
                  <select
                    id="logLevel"
                    value={selectedLogLevel}
                    onChange={(e) => setSelectedLogLevel(e.target.value)}
                    disabled={updatingLogging}
                    className="log-level-select"
                  >
                    <option value="DEBUG">DEBUG</option>
                    <option value="INFO">INFO</option>
                    <option value="WARNING">WARNING</option>
                    <option value="ERROR">ERROR</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>

                <div className="input-group checkbox-group">
                  <label htmlFor="enableTracing" className="checkbox-label">
                    <input
                      id="enableTracing"
                      type="checkbox"
                      checked={enableTracing}
                      onChange={(e) => setEnableTracing(e.target.checked)}
                      disabled={updatingLogging}
                    />
                    <span>Enable Function Tracing (use DEBUG level for trace output)</span>
                  </label>
                  <p className="tracing-warning">
                    ⚠️ Warning: Tracing logs function arguments which may contain sensitive data. 
                    Use only in development/debugging environments.
                  </p>
                </div>

                <button
                  className="test-button"
                  onClick={handleUpdateLogging}
                  disabled={updatingLogging}
                >
                  {updatingLogging ? 'Updating...' : 'Update Logging Configuration'}
                </button>

                {loggingUpdateSuccess && (
                  <div className="success-message">
                    {loggingUpdateSuccess}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Agent Prompts Section */}
      {activeSection === 'prompts' && (
        <div className="config-section">
          <h2>Agent Prompts Management</h2>
          <p>Customize the system prompts used by different agents in the incident resolution workflow.</p>
          
          {loadingPrompts ? (
            <p className="loading-text">Loading agent prompts...</p>
          ) : promptsError ? (
            <div className="config-error">
              <p><strong>Error:</strong> {promptsError}</p>
            </div>
          ) : agentPrompts ? (
            <div className="prompts-controls">
              <div className="agent-selector">
                <label htmlFor="agentSelect">Select Agent:</label>
                <select
                  id="agentSelect"
                  value={selectedAgent}
                  onChange={(e) => handleAgentChange(e.target.value)}
                  disabled={updatingPrompt || resettingPrompts}
                  className="agent-select"
                >
                  {Object.keys(agentPrompts.prompts).map((agentName) => (
                    <option key={agentName} value={agentName}>
                      {agentName.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      {agentPrompts.prompts[agentName].is_custom && ' ✏️'}
                    </option>
                  ))}
                </select>
              </div>

              {agentPrompts.prompts[selectedAgent] && (
                <div className="prompt-editor">
                  <div className="prompt-status">
                    <span className={`status-badge ${agentPrompts.prompts[selectedAgent].is_custom ? 'custom' : 'default'}`}>
                      {agentPrompts.prompts[selectedAgent].is_custom ? 'Custom Prompt' : 'Default Prompt'}
                    </span>
                  </div>

                  <div className="input-group">
                    <label htmlFor="promptText">Prompt Text:</label>
                    <textarea
                      id="promptText"
                      value={editedPrompt}
                      onChange={(e) => setEditedPrompt(e.target.value)}
                      disabled={updatingPrompt || resettingPrompts}
                      rows={12}
                      className="prompt-textarea"
                    />
                  </div>

                  <div className="prompt-actions">
                    <button
                      className="test-button"
                      onClick={handleUpdatePrompt}
                      disabled={updatingPrompt || resettingPrompts || editedPrompt === agentPrompts.prompts[selectedAgent].current}
                    >
                      {updatingPrompt ? 'Updating...' : 'Save Prompt'}
                    </button>

                    <button
                      className="reset-button"
                      onClick={handleResetPrompt}
                      disabled={updatingPrompt || resettingPrompts || !agentPrompts.prompts[selectedAgent].is_custom}
                    >
                      {resettingPrompts ? 'Resetting...' : 'Reset to Default'}
                    </button>

                    <button
                      className="reset-all-button"
                      onClick={handleResetAllPrompts}
                      disabled={updatingPrompt || resettingPrompts}
                    >
                      Reset All Prompts
                    </button>
                  </div>

                  {promptUpdateSuccess && (
                    <div className="success-message">
                      {promptUpdateSuccess}
                    </div>
                  )}

                  <div className="default-prompt-section">
                    <h3>Default Prompt:</h3>
                    <div className="default-prompt-display">
                      {agentPrompts.prompts[selectedAgent].default}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Accuracy Metrics Section */}
      {activeSection === 'accuracy' && (
        <div className="config-section">
          <h2>Result Accuracy Metrics</h2>
          <p>Track the accuracy of results returned from each category based on items excluded by users.</p>
          
          {loadingAccuracy ? (
            <p className="loading-text">Loading accuracy metrics...</p>
          ) : accuracyError ? (
            <div className="config-error">
              <p><strong>Error:</strong> {accuracyError}</p>
            </div>
          ) : accuracyMetrics ? (
            <div className="accuracy-metrics">
              {/* Overall Metrics */}
              <div className="overall-metrics">
                <h3>Overall Performance</h3>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <div className="metric-label">Overall Accuracy</div>
                    <div className={`metric-value large ${accuracyMetrics.overall_accuracy >= 80 ? 'good' : accuracyMetrics.overall_accuracy >= 60 ? 'medium' : 'poor'}`}>
                      {accuracyMetrics.overall_accuracy.toFixed(1)}%
                    </div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Total Items Returned</div>
                    <div className="metric-value">{accuracyMetrics.total_items_returned}</div>
                  </div>
                  <div className="metric-card">
                    <div className="metric-label">Total Exclusions</div>
                    <div className="metric-value">{accuracyMetrics.total_exclusions}</div>
                  </div>
                </div>
              </div>

              {/* Category Breakdown */}
              <div className="category-metrics">
                <h3>Accuracy by Category</h3>
                <div className="category-cards">
                  {accuracyMetrics.categories.map((category) => (
                    <div key={category.category} className="category-card">
                      <div className="category-header">
                        <h4>{category.category}</h4>
                        <div className={`accuracy-badge ${category.accuracy_score >= 80 ? 'good' : category.accuracy_score >= 60 ? 'medium' : 'poor'}`}>
                          {category.accuracy_score.toFixed(1)}%
                        </div>
                      </div>
                      <div className="category-stats">
                        <div className="stat-row">
                          <span className="stat-label">Items Returned:</span>
                          <span className="stat-value">{category.total_items_returned}</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Items Excluded:</span>
                          <span className="stat-value">{category.total_items_excluded}</span>
                        </div>
                        <div className="stat-row">
                          <span className="stat-label">Kept Items:</span>
                          <span className="stat-value">{category.total_items_returned - category.total_items_excluded}</span>
                        </div>
                      </div>
                      {/* Progress bar */}
                      <div className="accuracy-bar-container">
                        <div 
                          className={`accuracy-bar ${category.accuracy_score >= 80 ? 'good' : category.accuracy_score >= 60 ? 'medium' : 'poor'}`}
                          style={{ width: `${category.accuracy_score}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="metrics-info">
                <h3>About Accuracy Metrics</h3>
                <p>
                  Accuracy scores represent the percentage of returned items that were NOT excluded by users.
                  Higher scores indicate that the system is returning more relevant results.
                </p>
                <p>
                  When users delete/exclude items from the results, it indicates those items were not helpful
                  for resolving the incident. Tracking these exclusions helps identify which categories need
                  improvement.
                </p>
                <button className="test-button" onClick={fetchAccuracyMetrics}>
                  Refresh Metrics
                </button>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Prompt Logs Section */}
      {activeSection === 'prompt-logs' && (
        <div className="prompts-section">
          <h2>LLM Prompt Logs</h2>
          <p>View all prompts sent to the LLM, including RAG data context. This helps with debugging and understanding what information is being provided to the AI.</p>
          
          {loadingPromptLogs ? (
            <p className="loading-text">Loading prompt logs...</p>
          ) : promptLogsError ? (
            <div className="config-error">
              <p><strong>Error:</strong> {promptLogsError}</p>
            </div>
          ) : promptLogs ? (
            <div className="prompt-logs-container">
              <div className="prompt-logs-header">
                <div className="prompt-logs-stats">
                  <span className="stat-badge">Total Logs: {promptLogs.total_count}</span>
                  <span className="stat-badge">Synthesis: {promptLogs.logs.filter(l => l.prompt_type === 'synthesis').length}</span>
                  <span className="stat-badge">Chat: {promptLogs.logs.filter(l => l.prompt_type === 'chat').length}</span>
                </div>
                <div className="prompt-logs-actions">
                  <input
                    type="text"
                    placeholder="Filter by incident ID..."
                    value={promptLogFilter}
                    onChange={(e) => setPromptLogFilter(e.target.value)}
                    className="filter-input"
                  />
                  <button className="test-button" onClick={fetchPromptLogs}>
                    Refresh
                  </button>
                  <button className="reset-button" onClick={handleClearPromptLogs}>
                    Clear All Logs
                  </button>
                </div>
              </div>

              <div className="prompt-logs-list">
                {promptLogs.logs
                  .filter(log => !promptLogFilter || log.incident_id.toLowerCase().includes(promptLogFilter.toLowerCase()))
                  .map((log) => (
                    <div key={log.id} className="prompt-log-item">
                      <div className="prompt-log-header" onClick={() => setSelectedPromptLog(selectedPromptLog?.id === log.id ? null : log)}>
                        <div className="prompt-log-meta">
                          <span className={`prompt-type-badge ${log.prompt_type}`}>
                            {log.prompt_type === 'synthesis' ? '🔄 Synthesis' : '💬 Chat'}
                          </span>
                          <span className="prompt-log-incident">Incident: {log.incident_id}</span>
                          <span className="prompt-log-time">{new Date(log.timestamp).toLocaleString()}</span>
                        </div>
                        <span className="expand-icon">{selectedPromptLog?.id === log.id ? '▼' : '▶'}</span>
                      </div>
                      
                      {selectedPromptLog?.id === log.id && (
                        <div className="prompt-log-details">
                          {log.context_summary && (
                            <div className="prompt-log-section">
                              <h4>Context Summary</h4>
                              <p className="context-summary">{log.context_summary}</p>
                            </div>
                          )}
                          
                          <div className="prompt-log-section">
                            <h4>System Prompt</h4>
                            <pre className="prompt-content">{log.system_prompt}</pre>
                          </div>
                          
                          <div className="prompt-log-section">
                            <h4>User Message</h4>
                            <pre className="prompt-content">{log.user_message}</pre>
                          </div>
                          
                          {log.conversation_history && log.conversation_history.length > 0 && (
                            <div className="prompt-log-section">
                              <h4>Conversation History ({log.conversation_history.length} messages)</h4>
                              <div className="conversation-history">
                                {log.conversation_history.map((msg, idx) => (
                                  <div key={idx} className={`history-message ${msg.role}`}>
                                    <strong>{msg.role === 'user' ? 'User' : 'Assistant'}:</strong>
                                    <span>{msg.content}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
              </div>

              {promptLogs.logs.length === 0 && (
                <div className="no-logs-message">
                  <p>No prompt logs available yet. Logs will appear after LLM interactions.</p>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

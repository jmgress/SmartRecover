import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { LLMTestResponse, LLMConfigResponse, LoggingConfigResponse } from '../types/incident';
import './Admin.css';

export const Admin: React.FC = () => {
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

  useEffect(() => {
    fetchLLMConfig();
    fetchLoggingConfig();
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
    </div>
  );
};

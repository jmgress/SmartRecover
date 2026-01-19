import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { LLMTestResponse, LLMConfigResponse } from '../types/incident';
import './Admin.css';

export const Admin: React.FC = () => {
  const [testMessage, setTestMessage] = useState('Hello, are you working correctly?');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<LLMTestResponse | null>(null);
  const [llmConfig, setLlmConfig] = useState<LLMConfigResponse | null>(null);
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    fetchLLMConfig();
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
      <h1>Admin - LLM Communication Test</h1>
      
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

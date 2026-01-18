import React, { useState } from 'react';
import { api } from '../services/api';
import './Admin.css';

interface LLMTestResponse {
  status: string;
  provider: string;
  model: string;
  test_message: string;
  llm_response: string;
  error?: string;
}

export const Admin: React.FC = () => {
  const [testMessage, setTestMessage] = useState('Hello, are you working correctly?');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<LLMTestResponse | null>(null);

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
        provider: 'unknown',
        model: 'unknown',
        test_message: testMessage,
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

            <div className="result-item">
              <strong>Provider:</strong> {testResult.provider}
            </div>

            <div className="result-item">
              <strong>Model:</strong> {testResult.model}
            </div>

            <div className="result-item">
              <strong>Test Message:</strong> {testResult.test_message}
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

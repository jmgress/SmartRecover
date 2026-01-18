import { renderHook, act, waitFor } from '@testing-library/react';
import { useResolveIncident } from './useResolveIncident';
import { api } from '../services/api';

jest.mock('../services/api');

const mockResponse = {
  incident_id: 'INC001',
  resolution_steps: ['Step 1', 'Step 2'],
  related_knowledge: ['Knowledge 1'],
  correlated_changes: ['Change 1'],
  summary: 'Test summary',
  confidence: 0.95,
};

describe('useResolveIncident', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should resolve incident successfully', async () => {
    (api.resolveIncident as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useResolveIncident());

    expect(result.current.loading).toBe(false);

    let responseData;
    await act(async () => {
      responseData = await result.current.resolveIncident('INC001', 'Test query');
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(responseData).toEqual(mockResponse);
    expect(result.current.response).toEqual(mockResponse);
    expect(result.current.error).toBe(null);
  });

  it('should handle errors', async () => {
    const errorMessage = 'Failed to resolve';
    (api.resolveIncident as jest.Mock).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useResolveIncident());

    let caughtError;
    await act(async () => {
      try {
        await result.current.resolveIncident('INC001', 'Test query');
      } catch (err) {
        caughtError = err;
      }
    });

    expect(caughtError).toBeDefined();

    await waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
      expect(result.current.loading).toBe(false);
    });
  });
});

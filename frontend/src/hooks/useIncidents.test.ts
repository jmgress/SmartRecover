import { renderHook, waitFor } from '@testing-library/react';
import { useIncidents } from './useIncidents';
import { api } from '../services/api';

jest.mock('../services/api');

const mockIncidents = [
  {
    id: 'INC001',
    title: 'Test Incident',
    description: 'Test Description',
    severity: 'high',
    status: 'open',
    created_at: '2024-01-01T00:00:00Z',
    affected_services: ['service1'],
  },
];

describe('useIncidents', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch incidents successfully', async () => {
    (api.getIncidents as jest.Mock).mockResolvedValue(mockIncidents);

    const { result } = renderHook(() => useIncidents());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.incidents).toEqual(mockIncidents);
    expect(result.current.error).toBe(null);
  });

  it('should handle errors', async () => {
    const errorMessage = 'Failed to fetch';
    (api.getIncidents as jest.Mock).mockRejectedValue(new Error(errorMessage));

    const { result } = renderHook(() => useIncidents());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.incidents).toEqual([]);
    expect(result.current.error).toBe(errorMessage);
  });
});

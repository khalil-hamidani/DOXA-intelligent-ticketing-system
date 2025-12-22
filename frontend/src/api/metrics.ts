import api from './client';
import { MetricsOverview } from '../types';

export const metricsApi = {
  getOverview: async (): Promise<MetricsOverview> => {
    const response = await api.get<MetricsOverview>('/metrics/overview');
    return response.data;
  },
};

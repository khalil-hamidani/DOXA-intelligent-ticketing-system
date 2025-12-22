import api from './client';
import { AuthToken, User } from '../types';

export const authApi = {
  login: async (email: string, password: string): Promise<AuthToken> => {
    const response = await api.post<AuthToken>('/auth/login', { email, password });
    return response.data;
  },

  register: async (email: string, password: string): Promise<User> => {
    const response = await api.post<User>('/auth/register', { email, password });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

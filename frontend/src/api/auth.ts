import api from './client';
import { AuthToken, User, UserUpdate } from '../types';

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

  updateProfile: async (data: UserUpdate): Promise<User> => {
    const response = await api.put<User>('/auth/me', data);
    return response.data;
  },
};

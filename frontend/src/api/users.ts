import api from './client';

export interface UserData {
  id: number;
  email: string;
  role: 'CLIENT' | 'AGENT' | 'ADMIN';
  language: string;
  is_active: boolean;
  created_at: string;
  profile_picture_url?: string;
}

export interface UserStats {
  total: number;
  by_role: {
    CLIENT: number;
    AGENT: number;
    ADMIN: number;
  };
  active: number;
  inactive: number;
}

export const getUsers = async (role?: string): Promise<UserData[]> => {
  const params = role ? { role } : {};
  const response = await api.get('/users/', { params });
  return response.data;
};

export const getUserStats = async (): Promise<UserStats> => {
  const response = await api.get('/users/stats');
  return response.data;
};

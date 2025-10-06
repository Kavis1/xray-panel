import { create } from 'zustand';
import { authApi } from '@/services/api';
import type { Admin } from '@/types';

interface AuthState {
  admin: Admin | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  admin: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (username: string, password: string) => {
    set({ isLoading: true });
    try {
      const response = await authApi.login(username, password);
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      const meResponse = await authApi.getMe();
      set({
        admin: meResponse.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ admin: null, isAuthenticated: false });
  },

  fetchMe: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    set({ isLoading: true });
    try {
      const response = await authApi.getMe();
      set({
        admin: response.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ admin: null, isAuthenticated: false, isLoading: false });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },
}));

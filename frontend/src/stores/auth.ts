import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Tenant } from '@/types';
import { api } from '@/lib/api';

interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    business_name: string;
    business_email: string;
    business_phone?: string;
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    locale?: string;
  }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  loadTenant: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      tenant: null,
      isLoading: false,
      isAuthenticated: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await api.login(email, password);
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          });
          // Load tenant info
          await get().loadTenant();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data) => {
        set({ isLoading: true });
        try {
          const response = await api.register(data);
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          });
          // Load tenant info
          await get().loadTenant();
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: () => {
        api.logout();
        set({
          user: null,
          tenant: null,
          isAuthenticated: false,
        });
      },

      loadUser: async () => {
        if (!api.isAuthenticated()) {
          set({ isAuthenticated: false, user: null });
          return;
        }

        set({ isLoading: true });
        try {
          const user = await api.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch {
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },

      loadTenant: async () => {
        try {
          const tenant = await api.getCurrentTenant();
          set({ tenant });
        } catch {
          // Tenant load failed, but user might still be valid
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tenant: state.tenant,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

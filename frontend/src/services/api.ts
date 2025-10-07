import axios from 'axios';
import type { User, Node, Inbound, Admin, AuthTokens } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username: string, password: string) =>
    api.post<AuthTokens>('/auth/login', { username, password }),
  
  getMe: () => api.get<Admin>('/auth/me'),
  
  logout: () => api.post('/auth/logout'),
};

export const usersApi = {
  list: (params?: any) => api.get<{ total: number; items: User[] }>('/users/', { params }),
  
  get: (id: number) => api.get<User>(`/users/${id}`),
  
  create: (data: any) => api.post<User>('/users/', data),
  
  update: (id: number, data: any) => api.patch<User>(`/users/${id}`, data),
  
  delete: (id: number) => api.delete(`/users/${id}`),
  
  resetTraffic: (id: number) => api.post<User>(`/users/${id}/reset-traffic`),
  
  revokeSubscription: (id: number) => api.post(`/users/${id}/revoke-sub`),
  
  getProxies: (id: number) => api.get<any>(`/users/${id}/proxies`),
  
  getInbounds: (id: number) => api.get<any>(`/users/${id}/inbounds`),
  
  assignInbounds: (id: number, inboundIds: number[]) =>
    api.post<any>(`/users/${id}/assign-inbounds`, { inbound_ids: inboundIds }),
};

export const nodesApi = {
  list: (params?: any) => api.get<Node[]>('/nodes/', { params }),
  
  get: (id: number) => api.get<Node>(`/nodes/${id}`),
  
  create: (data: any) => api.post<Node>('/nodes/', data),
  
  update: (id: number, data: any) => api.patch<Node>(`/nodes/${id}`, data),
  
  delete: (id: number) => api.delete(`/nodes/${id}`),
  
  connect: (id: number) => api.post(`/nodes/${id}/connect`),
  
  disconnect: (id: number) => api.post(`/nodes/${id}/disconnect`),
  
  generateSSL: (nodeName: string, nodeAddress: string) =>
    api.post<{
      success: boolean;
      name: string;
      address: string;
      ca_certificate: string;
      client_certificate: string;
      client_key: string;
    }>('/nodes/generate-ssl', null, {
      params: { node_name: nodeName, node_address: nodeAddress },
    }),
};

export const inboundsApi = {
  list: () => api.get<Inbound[]>('/inbounds/'),
  
  get: (id: number) => api.get<Inbound>(`/inbounds/${id}`),
  
  create: (data: any) => api.post<Inbound>('/inbounds/', data),
  
  update: (id: number, data: any) => api.patch<Inbound>(`/inbounds/${id}`, data),
  
  delete: (id: number) => api.delete(`/inbounds/${id}`),
};

export const adminsApi = {
  list: () => api.get<Admin[]>('/admins/'),
  
  create: (data: any) => api.post<Admin>('/admins/', data),
  
  update: (id: number, data: any) => api.patch<Admin>(`/admins/${id}`, data),
  
  delete: (id: number) => api.delete(`/admins/${id}`),
};

export const templatesApi = {
  list: () => api.get<any[]>('/templates/'),
  
  generate: (templateId: string, params?: any) => 
    api.post<any>('/templates/generate', { template_id: templateId, ...params }),
  
  getRealityKeys: () => api.get<any>('/templates/reality/keys'),
};

export default api;

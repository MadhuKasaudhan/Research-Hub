import api from './api';
import type { Workspace, WorkspaceCreate, WorkspaceUpdate, WorkspaceStats, PaginatedResponse } from '../types';

export const workspaceApi = {
  async list(page = 1, size = 20): Promise<PaginatedResponse<Workspace>> {
    const response = await api.get<PaginatedResponse<Workspace>>('/workspaces', {
      params: { page, size },
    });
    return response.data;
  },

  async get(id: string): Promise<Workspace> {
    const response = await api.get<Workspace>(`/workspaces/${id}`);
    return response.data;
  },

  async create(data: WorkspaceCreate): Promise<Workspace> {
    const response = await api.post<Workspace>('/workspaces', data);
    return response.data;
  },

  async update(id: string, data: WorkspaceUpdate): Promise<Workspace> {
    const response = await api.put<Workspace>(`/workspaces/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/workspaces/${id}`);
  },

  async getStats(id: string): Promise<WorkspaceStats> {
    const response = await api.get<WorkspaceStats>(`/workspaces/${id}/stats`);
    return response.data;
  },
};

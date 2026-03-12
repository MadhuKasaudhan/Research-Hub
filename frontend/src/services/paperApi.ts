import api from './api';
import type { Paper, PaperUpdate, PaperUploadResponse, PaperStatus, PaperChunk, PaginatedResponse } from '../types';

export const paperApi = {
  async list(
    workspaceId: string,
    params: {
      page?: number;
      size?: number;
      search?: string;
      year?: number;
      tags?: string;
      sort_by?: string;
      order?: string;
    } = {}
  ): Promise<PaginatedResponse<Paper>> {
    const response = await api.get<PaginatedResponse<Paper>>(
      `/workspaces/${workspaceId}/papers`,
      { params }
    );
    return response.data;
  },

  async upload(workspaceId: string, file: File): Promise<PaperUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<PaperUploadResponse>(
      `/workspaces/${workspaceId}/papers/upload`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  async get(paperId: string): Promise<Paper> {
    const response = await api.get<Paper>(`/papers/${paperId}`);
    return response.data;
  },

  async update(paperId: string, data: PaperUpdate): Promise<Paper> {
    const response = await api.put<Paper>(`/papers/${paperId}`, data);
    return response.data;
  },

  async delete(paperId: string): Promise<void> {
    await api.delete(`/papers/${paperId}`);
  },

  async getStatus(paperId: string): Promise<PaperStatus> {
    const response = await api.get<PaperStatus>(`/papers/${paperId}/status`);
    return response.data;
  },

  async getChunks(paperId: string): Promise<PaperChunk[]> {
    const response = await api.get<PaperChunk[]>(`/papers/${paperId}/chunks`);
    return response.data;
  },
};

import api from "./api";
import type {
  Conversation,
  ConversationCreate,
  Message,
  MessageCreate,
  ChatResponse,
  AnalysisRequest,
  AnalysisResponse,
  SynthesisRequest,
  SynthesisResponse,
  SearchResult,
} from "../types";

export const chatApi = {
  async createConversation(
    workspaceId: string,
    data: ConversationCreate,
  ): Promise<Conversation> {
    const response = await api.post<Conversation>(
      `/workspaces/${workspaceId}/conversations`,
      data,
    );
    return response.data;
  },

  async listConversations(
    workspaceId: string,
    page = 1,
    size = 20,
  ): Promise<Conversation[]> {
    const response = await api.get<Conversation[]>(
      `/workspaces/${workspaceId}/conversations`,
      { params: { page, size } },
    );
    return response.data;
  },

  async getConversation(
    conversationId: string,
  ): Promise<{ conversation: Conversation; messages: Message[] }> {
    const response = await api.get<{
      conversation: Conversation;
      messages: Message[];
    }>(`/conversations/${conversationId}`);
    return response.data;
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/conversations/${conversationId}`);
  },

  async sendMessage(
    conversationId: string,
    data: MessageCreate,
  ): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>(
      `/conversations/${conversationId}/messages`,
      data,
    );
    return response.data;
  },

  async analyzePaper(
    paperId: string,
    data: AnalysisRequest,
  ): Promise<AnalysisResponse> {
    const response = await api.post<AnalysisResponse>(
      `/papers/${paperId}/analyze`,
      data,
    );
    return response.data;
  },

  async synthesize(
    workspaceId: string,
    data: SynthesisRequest,
  ): Promise<SynthesisResponse> {
    const response = await api.post<SynthesisResponse>(
      `/workspaces/${workspaceId}/synthesize`,
      data,
    );
    return response.data;
  },

  async search(
    workspaceId: string,
    query: string,
    limit = 10,
    paperIds?: string[],
  ): Promise<SearchResult[]> {
    const response = await api.get<{
      query: string;
      results: SearchResult[];
      total: number;
    }>(`/workspaces/${workspaceId}/search`, {
      params: { q: query, limit, paper_ids: paperIds?.join(",") },
    });
    return response.data.results;
  },
};

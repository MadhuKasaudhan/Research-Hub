// User types
export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserUpdate {
  full_name?: string;
  password?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Workspace types
export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  color: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  paper_count: number;
  conversation_count: number;
}

export interface WorkspaceCreate {
  name: string;
  description?: string;
  color?: string;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string;
  color?: string;
}

export interface WorkspaceStats {
  paper_count: number;
  conversation_count: number;
  last_activity: string | null;
}

// Paper types
export interface Paper {
  id: string;
  title: string;
  authors: string[] | null;
  abstract: string | null;
  file_name: string;
  file_size: number;
  mime_type: string;
  workspace_id: string;
  uploaded_by: string;
  year: number | null;
  journal: string | null;
  doi: string | null;
  tags: string[] | null;
  is_processed: boolean;
  processing_status: string;
  processing_error: string | null;
  created_at: string;
  updated_at: string;
  chunk_count: number;
}

export interface PaperUpdate {
  title?: string;
  authors?: string[];
  abstract?: string;
  year?: number;
  journal?: string;
  doi?: string;
  tags?: string[];
}

export interface PaperUploadResponse {
  id: string;
  file_name: string;
  processing_status: string;
  message: string;
}

export interface PaperStatus {
  id: string;
  processing_status: string;
  processing_error: string | null;
  is_processed: boolean;
}

export interface PaperChunk {
  id: string;
  paper_id: string;
  chunk_index: number;
  content: string;
}

// Conversation types
export interface Conversation {
  id: string;
  title: string;
  workspace_id: string;
  paper_ids: string[] | null;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string | null;
}

export interface ConversationCreate {
  title?: string;
  paper_ids?: string[];
}

// Message types
export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata: Record<string, unknown> | null;
  tokens_used: number | null;
  created_at: string;
  sources?: string[] | null;
}

export interface MessageCreate {
  content: string;
  paper_ids?: string[];
}

export interface ChatResponse {
  message_id: string;
  content: string;
  sources: string[];
  tokens_used: number;
}

// Analysis types
export interface AnalysisRequest {
  analysis_type: 'summary' | 'key_findings' | 'methodology' | 'critique' | 'concepts';
}

export interface AnalysisResponse {
  result: string;
  analysis_type: string;
  tokens_used: number;
}

// Synthesis types
export interface SynthesisRequest {
  paper_ids: string[];
  synthesis_type: 'compare' | 'themes' | 'timeline' | 'gaps';
}

export interface SynthesisResponse {
  result: string;
  synthesis_type: string;
  papers_used: string[];
  tokens_used: number;
}

// Search types
export interface SearchResult {
  chunk: string;
  score: number;
  paper_id: string;
  paper_title: string;
  chunk_index: number;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// API Error
export interface ApiError {
  detail: string;
  code: string;
  timestamp: string;
}

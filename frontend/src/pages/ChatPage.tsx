import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { chatApi } from '../services/chatApi';
import { paperApi } from '../services/paperApi';
import { MessageBubble } from '../components/MessageBubble';
import { ChatInput } from '../components/ChatInput';
import type { Conversation, Paper } from '../types';
import {
  ArrowLeft, Plus, MessageSquare, Trash2, FileText,
  Loader2, Bot, Menu, X,
} from 'lucide-react';

export function ChatPage() {
  const { workspaceId, conversationId } = useParams<{
    workspaceId: string;
    conversationId: string;
  }>();
  const navigate = useNavigate();
  const {
    messages, conversation, isLoading, error,
    loadConversation, sendMessage, setError,
  } = useChat();
  
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaperIds, setSelectedPaperIds] = useState<string[]>([]);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (workspaceId) {
      loadConversationsList();
      loadPapers();
    }
  }, [workspaceId]);

  useEffect(() => {
    if (conversationId) {
      loadConversation(conversationId);
    }
  }, [conversationId, loadConversation]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversationsList = async () => {
    try {
      const convos = await chatApi.listConversations(workspaceId!);
      setConversations(convos);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadPapers = async () => {
    try {
      const response = await paperApi.list(workspaceId!);
      setPapers(response.items.filter((p) => p.is_processed));
    } catch (err) {
      console.error('Failed to load papers:', err);
    }
  };

  const handleNewConversation = async () => {
    try {
      const conv = await chatApi.createConversation(workspaceId!, {
        title: 'New Conversation',
      });
      await loadConversationsList();
      navigate(`/workspace/${workspaceId}/chat/${conv.id}`);
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    try {
      await chatApi.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (convId === conversationId) {
        navigate(`/workspace/${workspaceId}/chat/${conversations[0]?.id || ''}`);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSend = async (content: string) => {
    await sendMessage(content, selectedPaperIds.length > 0 ? selectedPaperIds : undefined);
  };

  const togglePaper = (paperId: string) => {
    setSelectedPaperIds((prev) =>
      prev.includes(paperId)
        ? prev.filter((id) => id !== paperId)
        : [...prev, paperId]
    );
  };

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Left Panel — Conversation List (hidden on mobile) */}
      <aside className="hidden md:flex w-72 bg-white border-r border-gray-200 flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => navigate(`/workspace/${workspaceId}`)}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Workspace
          </button>
          <button
            onClick={handleNewConversation}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => navigate(`/workspace/${workspaceId}/chat/${conv.id}`)}
              className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer group transition-colors ${
                conv.id === conversationId
                  ? 'bg-primary-50 text-primary-700'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{conv.title}</p>
                {conv.last_message_preview && (
                  <p className="text-xs text-gray-500 truncate mt-0.5">{conv.last_message_preview}</p>
                )}
              </div>
              <button
                onClick={(e) => handleDeleteConversation(conv.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 rounded"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Center Panel — Chat Messages */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile top bar */}
        <div className="md:hidden flex items-center gap-2 px-4 py-2 bg-white border-b border-gray-200">
          <button
            onClick={() => setShowMobileSidebar(!showMobileSidebar)}
            className="p-1 text-gray-600 hover:text-gray-900 rounded"
          >
            {showMobileSidebar ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="text-sm font-medium text-gray-700 truncate">
            {conversation?.title || 'Conversations'}
          </span>
        </div>

        {/* Mobile sidebar overlay */}
        {showMobileSidebar && (
          <div className="md:hidden absolute inset-0 z-40 flex">
            <div className="w-72 bg-white border-r border-gray-200 flex flex-col shadow-xl">
              <div className="p-4 border-b border-gray-200">
                <button
                  onClick={() => { navigate(`/workspace/${workspaceId}`); setShowMobileSidebar(false); }}
                  className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-3"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Workspace
                </button>
                <button
                  onClick={() => { handleNewConversation(); setShowMobileSidebar(false); }}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
                >
                  <Plus className="w-4 h-4" />
                  New Conversation
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => { navigate(`/workspace/${workspaceId}/chat/${conv.id}`); setShowMobileSidebar(false); }}
                    className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer group transition-colors ${
                      conv.id === conversationId
                        ? 'bg-primary-50 text-primary-700'
                        : 'hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{conv.title}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex-1 bg-black/20" onClick={() => setShowMobileSidebar(false)} />
          </div>
        )}

        {conversation ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-3">
              <h2 className="font-medium text-gray-900">{conversation.title}</h2>
              <p className="text-xs text-gray-500">{messages.length} messages</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-20">
                  <Bot className="w-12 h-12 text-gray-300 mx-auto" />
                  <h3 className="mt-4 text-sm font-medium text-gray-900">
                    Ask anything about your research papers
                  </h3>
                  <p className="mt-1 text-xs text-gray-500">
                    Select papers from the right panel to focus your conversation.
                  </p>
                </div>
              )}
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  AI is thinking...
                </div>
              )}
              {error && (
                <div className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
                  {error}
                  <button
                    onClick={() => setError(null)}
                    className="ml-2 text-red-500 hover:text-red-700 underline"
                  >
                    Dismiss
                  </button>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <ChatInput onSend={handleSend} isLoading={isLoading} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <MessageSquare className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="mt-3 text-sm">Select or create a conversation</p>
            </div>
          </div>
        )}
      </div>

      {/* Right Panel — Paper Context (hidden on mobile) */}
      <aside className="hidden lg:flex w-72 bg-white border-l border-gray-200 flex-col">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-medium text-gray-900 text-sm">Papers in Context</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            {selectedPaperIds.length === 0
              ? 'All papers will be searched'
              : `${selectedPaperIds.length} paper(s) selected`}
          </p>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {papers.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8">
              No processed papers available
            </p>
          ) : (
            papers.map((paper) => (
              <label
                key={paper.id}
                className={`flex items-start gap-2.5 p-2.5 rounded-lg cursor-pointer transition-colors ${
                  selectedPaperIds.includes(paper.id)
                    ? 'bg-primary-50 border border-primary-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedPaperIds.includes(paper.id)}
                  onChange={() => togglePaper(paper.id)}
                  className="mt-0.5 h-4 w-4 text-primary-600 rounded border-gray-300"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-900 line-clamp-2">{paper.title}</p>
                  {paper.authors && (
                    <p className="text-xs text-gray-500 truncate mt-0.5">
                      {paper.authors.slice(0, 2).join(', ')}
                    </p>
                  )}
                </div>
              </label>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}

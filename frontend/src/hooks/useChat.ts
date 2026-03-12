import { useState, useCallback } from 'react';
import { chatApi } from '../services/chatApi';
import type { Message, Conversation } from '../types';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadConversation = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await chatApi.getConversation(conversationId);
      setConversation(data.conversation);
      setMessages(data.messages);
    } catch (err) {
      setError('Failed to load conversation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (content: string, paperIds?: string[]) => {
    if (!conversation) return;

    // Optimistically add user message
    const optimisticMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversation.id,
      role: 'user',
      content,
      metadata: null,
      tokens_used: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.sendMessage(conversation.id, {
        content,
        paper_ids: paperIds,
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: response.message_id,
        conversation_id: conversation.id,
        role: 'assistant',
        content: response.content,
        metadata: { sources: response.sources },
        tokens_used: response.tokens_used,
        created_at: new Date().toISOString(),
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      // Remove optimistic message on error
      setMessages((prev) => prev.filter((m) => m.id !== optimisticMessage.id));
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [conversation]);

  const createConversation = useCallback(async (
    workspaceId: string,
    paperIds?: string[],
    title?: string,
  ) => {
    try {
      const conv = await chatApi.createConversation(workspaceId, {
        title: title || 'New Conversation',
        paper_ids: paperIds,
      });
      setConversation(conv);
      setMessages([]);
      return conv;
    } catch (err) {
      setError('Failed to create conversation');
      console.error(err);
      return null;
    }
  }, []);

  return {
    messages,
    conversation,
    isLoading,
    error,
    loadConversation,
    sendMessage,
    createConversation,
    setError,
  };
}

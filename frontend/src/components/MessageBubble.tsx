import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, ChevronDown, ChevronUp, Bot, User, Zap } from 'lucide-react';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  const sources = message.sources || (message.metadata as Record<string, unknown>)?.sources as string[] | undefined;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-primary-100' : 'bg-gray-100'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-primary-600" />
        ) : (
          <Bot className="w-4 h-4 text-gray-600" />
        )}
      </div>

      {/* Message Content */}
      <div className={`max-w-[75%] ${isUser ? 'text-right' : ''}`}>
        <div className={`rounded-xl px-4 py-3 ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-white border border-gray-200'
        }`}>
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none text-gray-700">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Sources (assistant only) */}
        {!isUser && sources && sources.length > 0 && (
          <div className="mt-1.5">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
            >
              {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {sources.length} source{sources.length > 1 ? 's' : ''}
            </button>
            {showSources && (
              <div className="mt-1 space-y-0.5">
                {sources.map((source, i) => (
                  <p key={i} className="text-xs text-gray-500 pl-4">
                    - {source}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className={`flex items-center gap-2 mt-1 ${isUser ? 'justify-end' : ''}`}>
          <span className="text-xs text-gray-400">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          {!isUser && message.tokens_used && (
            <span className="flex items-center gap-0.5 text-xs text-gray-400">
              <Zap className="w-3 h-3" />
              {message.tokens_used}
            </span>
          )}
          {!isUser && (
            <button onClick={handleCopy} className="text-gray-400 hover:text-gray-600">
              {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

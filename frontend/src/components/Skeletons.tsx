import React from 'react';

/** Reusable skeleton pulse block. */
const Pulse: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse rounded bg-gray-200 ${className}`} />
);

// ---------------------------------------------------------------------------
// WorkspaceCard skeleton
// ---------------------------------------------------------------------------

export const WorkspaceCardSkeleton: React.FC = () => (
  <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
    <Pulse className="mb-3 h-5 w-3/4" />
    <Pulse className="mb-2 h-3 w-full" />
    <Pulse className="mb-4 h-3 w-2/3" />
    <div className="flex gap-4">
      <Pulse className="h-4 w-16" />
      <Pulse className="h-4 w-16" />
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// PaperCard skeleton
// ---------------------------------------------------------------------------

export const PaperCardSkeleton: React.FC = () => (
  <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
    <div className="flex items-start gap-3">
      <Pulse className="h-10 w-10 flex-shrink-0 rounded-lg" />
      <div className="flex-1">
        <Pulse className="mb-2 h-4 w-5/6" />
        <Pulse className="mb-2 h-3 w-1/2" />
        <Pulse className="h-3 w-1/3" />
      </div>
    </div>
    <div className="mt-3 flex gap-2">
      <Pulse className="h-5 w-14 rounded-full" />
      <Pulse className="h-5 w-20 rounded-full" />
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// MessageBubble skeleton
// ---------------------------------------------------------------------------

export const MessageBubbleSkeleton: React.FC<{ align?: 'left' | 'right' }> = ({
  align = 'left',
}) => (
  <div className={`flex ${align === 'right' ? 'justify-end' : 'justify-start'}`}>
    <div
      className={`max-w-[70%] rounded-2xl p-4 ${
        align === 'right' ? 'bg-blue-100' : 'bg-gray-100'
      }`}
    >
      <Pulse className="mb-2 h-3 w-48" />
      <Pulse className="mb-2 h-3 w-64" />
      <Pulse className="h-3 w-36" />
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Generic list skeleton
// ---------------------------------------------------------------------------

export const ListSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <Pulse key={i} className="h-16 w-full rounded-xl" />
    ))}
  </div>
);

export default {
  WorkspaceCardSkeleton,
  PaperCardSkeleton,
  MessageBubbleSkeleton,
  ListSkeleton,
};

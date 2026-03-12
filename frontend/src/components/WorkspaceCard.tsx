import { useState } from 'react';
import { FileText, MessageSquare, Trash2, Clock } from 'lucide-react';
import { workspaceApi } from '../services/workspaceApi';
import type { Workspace } from '../types';

interface WorkspaceCardProps {
  workspace: Workspace;
  onClick: () => void;
  onDelete: () => void;
}

export function WorkspaceCard({ workspace, onClick, onDelete }: WorkspaceCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Delete this workspace and all its papers?')) return;
    setIsDeleting(true);
    try {
      await workspaceApi.delete(workspace.id);
      onDelete();
    } catch (error) {
      console.error('Failed to delete workspace:', error);
      setIsDeleting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-xl border border-gray-200 hover:border-gray-300 hover:shadow-md transition-all cursor-pointer group"
    >
      <div className="h-2 rounded-t-xl" style={{ backgroundColor: workspace.color }} />
      <div className="p-5">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-gray-900 truncate flex-1">
            {workspace.name}
          </h3>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="opacity-0 group-hover:opacity-100 p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
        
        {workspace.description && (
          <p className="mt-1 text-sm text-gray-500 line-clamp-2">{workspace.description}</p>
        )}

        <div className="mt-4 flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1.5">
            <FileText className="w-4 h-4" />
            <span>{workspace.paper_count} papers</span>
          </div>
          <div className="flex items-center gap-1.5">
            <MessageSquare className="w-4 h-4" />
            <span>{workspace.conversation_count} chats</span>
          </div>
        </div>
        
        <div className="mt-3 flex items-center gap-1.5 text-xs text-gray-400">
          <Clock className="w-3.5 h-3.5" />
          <span>Updated {formatDate(workspace.updated_at)}</span>
        </div>
      </div>
    </div>
  );
}

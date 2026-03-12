import { FileText, Trash2, Loader2, Tag, Calendar, BookOpen, Search } from 'lucide-react';
import type { Paper } from '../types';

interface PaperCardProps {
  paper: Paper;
  onClick: () => void;
  onDelete: (paperId: string) => void;
}

export function PaperCard({ paper, onClick, onDelete }: PaperCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this paper?')) {
      onDelete(paper.id);
    }
  };

  const statusColors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-700',
    extracting: 'bg-blue-100 text-blue-700',
    chunking: 'bg-blue-100 text-blue-700',
    embedding: 'bg-blue-100 text-blue-700',
    analyzing: 'bg-purple-100 text-purple-700',
    completed: 'bg-green-100 text-green-700',
    failed: 'bg-red-100 text-red-700',
  };

  const isProcessing = !paper.is_processed && paper.processing_status !== 'failed';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer p-4 group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">{paper.title}</h4>
          {paper.authors && paper.authors.length > 0 && (
            <p className="text-sm text-gray-500 truncate mt-0.5">
              {paper.authors.join(', ')}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[paper.processing_status] || 'bg-gray-100 text-gray-700'}`}>
            {isProcessing && <Loader2 className="w-3 h-3 animate-spin inline mr-1" />}
            {paper.processing_status}
          </span>
          <button
            onClick={handleDelete}
            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 rounded transition-all"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
        {paper.year && (
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {paper.year}
          </span>
        )}
        {paper.journal && (
          <span className="flex items-center gap-1">
            <BookOpen className="w-3.5 h-3.5" />
            <span className="truncate max-w-[120px]">{paper.journal}</span>
          </span>
        )}
        <span className="flex items-center gap-1">
          <FileText className="w-3.5 h-3.5" />
          {(paper.file_size / 1024 / 1024).toFixed(1)} MB
        </span>
      </div>

      {paper.tags && paper.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {paper.tags.slice(0, 4).map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
              <Tag className="w-3 h-3" />
              {tag}
            </span>
          ))}
          {paper.tags.length > 4 && (
            <span className="text-xs text-gray-400">+{paper.tags.length - 4}</span>
          )}
        </div>
      )}
    </div>
  );
}

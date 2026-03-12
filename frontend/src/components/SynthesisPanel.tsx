import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../services/chatApi';
import type { Paper } from '../types';
import { Beaker, Loader2, Zap } from 'lucide-react';

interface SynthesisPanelProps {
  workspaceId: string;
  papers: Paper[];
}

const SYNTHESIS_TYPES = [
  { id: 'compare' as const, label: 'Compare', description: 'Side-by-side comparison of papers' },
  { id: 'themes' as const, label: 'Themes', description: 'Find common themes across papers' },
  { id: 'timeline' as const, label: 'Timeline', description: 'Build research evolution timeline' },
  { id: 'gaps' as const, label: 'Gaps', description: 'Identify research gaps' },
];

export function SynthesisPanel({ workspaceId, papers }: SynthesisPanelProps) {
  const [selectedPaperIds, setSelectedPaperIds] = useState<string[]>([]);
  const [synthesisType, setSynthesisType] = useState<'compare' | 'themes' | 'timeline' | 'gaps'>('compare');
  const [result, setResult] = useState<string | null>(null);
  const [tokensUsed, setTokensUsed] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const processedPapers = papers.filter((p) => p.is_processed);

  const togglePaper = (paperId: string) => {
    setSelectedPaperIds((prev) =>
      prev.includes(paperId)
        ? prev.filter((id) => id !== paperId)
        : [...prev, paperId]
    );
  };

  const handleSynthesize = async () => {
    if (selectedPaperIds.length < 2) return;
    setIsLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await chatApi.synthesize(workspaceId, {
        paper_ids: selectedPaperIds,
        synthesis_type: synthesisType,
      });
      setResult(response.result);
      setTokensUsed(response.tokens_used);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Synthesis failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Cross-Paper Synthesis</h3>
      
      {/* Paper Selection */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Select Papers (at least 2)
        </h4>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {processedPapers.length === 0 ? (
            <p className="text-sm text-gray-500">No processed papers available for synthesis.</p>
          ) : (
            processedPapers.map((paper) => (
              <label
                key={paper.id}
                className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedPaperIds.includes(paper.id)}
                  onChange={() => togglePaper(paper.id)}
                  className="h-4 w-4 text-primary-600 rounded border-gray-300"
                />
                <span className="text-sm text-gray-700 truncate">{paper.title}</span>
              </label>
            ))
          )}
        </div>
      </div>

      {/* Synthesis Type */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Synthesis Type</h4>
        <div className="grid grid-cols-2 gap-2">
          {SYNTHESIS_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => setSynthesisType(type.id)}
              className={`p-3 rounded-lg border text-left transition-colors ${
                synthesisType === type.id
                  ? 'border-primary-300 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className="text-sm font-medium text-gray-900">{type.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{type.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={handleSynthesize}
        disabled={selectedPaperIds.length < 2 || isLoading}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm font-medium mb-4"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Synthesizing...
          </>
        ) : (
          <>
            <Beaker className="w-4 h-4" />
            Run Synthesis
          </>
        )}
      </button>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Synthesis Result</h4>
            {tokensUsed > 0 && (
              <span className="flex items-center gap-1 text-xs text-gray-400">
                <Zap className="w-3 h-3" />
                {tokensUsed} tokens
              </span>
            )}
          </div>
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{result}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}

import { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../services/chatApi';
import { Sparkles, Loader2, Copy, Check, RefreshCw, Zap } from 'lucide-react';

interface AnalysisPanelProps {
  paperId: string;
  analysisType: string;
  isProcessed: boolean;
}

// Cache results to avoid re-fetching on tab switch
const analysisCache = new Map<string, { result: string; tokens: number }>();

export function AnalysisPanel({ paperId, analysisType, isProcessed }: AnalysisPanelProps) {
  const cacheKey = `${paperId}_${analysisType}`;
  const cached = analysisCache.get(cacheKey);
  
  const [result, setResult] = useState<string>(cached?.result || '');
  const [tokensUsed, setTokensUsed] = useState<number>(cached?.tokens || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const prevKeyRef = useRef(cacheKey);

  // Update state when tab changes
  if (prevKeyRef.current !== cacheKey) {
    prevKeyRef.current = cacheKey;
    const c = analysisCache.get(cacheKey);
    if (c) {
      if (result !== c.result) setResult(c.result);
      if (tokensUsed !== c.tokens) setTokensUsed(c.tokens);
    } else {
      if (result !== '') setResult('');
      if (tokensUsed !== 0) setTokensUsed(0);
    }
  }

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await chatApi.analyzePaper(paperId, {
        analysis_type: analysisType as 'summary' | 'key_findings' | 'methodology' | 'critique' | 'concepts',
      });
      setResult(response.result);
      setTokensUsed(response.tokens_used);
      analysisCache.set(cacheKey, { result: response.result, tokens: response.tokens_used });
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isProcessed) {
    return (
      <div className="text-center py-8 text-sm text-gray-500">
        <Sparkles className="w-8 h-8 text-gray-300 mx-auto mb-2" />
        Paper is still being processed. Analysis will be available once processing completes.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600 mx-auto" />
        <p className="mt-3 text-sm text-gray-500">Generating {analysisType.replace('_', ' ')} analysis...</p>
        <p className="text-xs text-gray-400 mt-1">This may take 10-20 seconds</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-red-600 mb-3">{error}</p>
        <button
          onClick={handleGenerate}
          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-8">
        <Sparkles className="w-10 h-10 text-gray-300 mx-auto" />
        <p className="mt-3 text-sm text-gray-600">
          Generate an AI-powered {analysisType.replace('_', ' ')} of this paper
        </p>
        <button
          onClick={handleGenerate}
          className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700"
        >
          <Sparkles className="w-4 h-4" />
          Generate Analysis
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {tokensUsed > 0 && (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Zap className="w-3 h-3" />
              {tokensUsed} tokens
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
            title="Copy to clipboard"
          >
            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={handleGenerate}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded"
            title="Regenerate"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="prose prose-sm max-w-none text-gray-700">
        <ReactMarkdown>{result}</ReactMarkdown>
      </div>
    </div>
  );
}

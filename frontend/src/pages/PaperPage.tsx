import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { paperApi } from "../services/paperApi";
import { AnalysisPanel } from "../components/AnalysisPanel";
import { ProcessingStatus } from "../components/ProcessingStatus";
import type { Paper } from "../types";
import {
  ArrowLeft,
  Download,
  FileText,
  Calendar,
  BookOpen,
  Users,
  Tag,
  Hash,
  Loader2,
  ExternalLink,
} from "lucide-react";

const ANALYSIS_TABS = [
  { id: "summary" as const, label: "Summary" },
  { id: "key_findings" as const, label: "Key Findings" },
  { id: "methodology" as const, label: "Methodology" },
  { id: "critique" as const, label: "Critique" },
  { id: "concepts" as const, label: "Concepts" },
];

export function PaperPage() {
  const { workspaceId, paperId } = useParams<{
    workspaceId: string;
    paperId: string;
  }>();
  const navigate = useNavigate();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState<string>("summary");

  useEffect(() => {
    if (paperId) loadPaper();
  }, [paperId]);

  const loadPaper = async () => {
    setIsLoading(true);
    try {
      const data = await paperApi.get(paperId!);
      setPaper(data);
    } catch (error) {
      console.error("Failed to load paper:", error);
      navigate(`/workspace/${workspaceId}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading || !paper) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <button
          onClick={() => navigate(`/workspace/${workspaceId}`)}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Workspace
        </button>
        <h1 className="text-xl font-bold text-gray-900">{paper.title}</h1>
        {paper.authors && paper.authors.length > 0 && (
          <p className="text-sm text-gray-600 mt-1">
            {paper.authors.join(", ")}
          </p>
        )}
      </header>

      {/* Content */}
      <div className="flex flex-col lg:flex-row gap-6 p-6 max-w-7xl mx-auto">
        {/* Left Panel — Paper Info (60%) */}
        <div className="lg:w-3/5 space-y-6">
          {/* Processing Status */}
          {!paper.is_processed && (
            <ProcessingStatus paperId={paper.id} onComplete={loadPaper} />
          )}

          {/* Metadata */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Paper Details</h3>
            <div className="grid grid-cols-2 gap-4">
              {paper.year && (
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Year:</span>
                  <span className="font-medium">{paper.year}</span>
                </div>
              )}
              {paper.journal && (
                <div className="flex items-center gap-2 text-sm">
                  <BookOpen className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">Journal:</span>
                  <span className="font-medium truncate">{paper.journal}</span>
                </div>
              )}
              {paper.doi && (
                <div className="flex items-center gap-2 text-sm">
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                  <span className="text-gray-600">DOI:</span>
                  <span className="font-medium text-primary-600 truncate">
                    {paper.doi}
                  </span>
                </div>
              )}
              <div className="flex items-center gap-2 text-sm">
                <FileText className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">File:</span>
                <span className="font-medium">
                  {paper.file_name} ({formatFileSize(paper.file_size)})
                </span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <Hash className="w-4 h-4 text-gray-400" />
                <span className="text-gray-600">Chunks:</span>
                <span className="font-medium">{paper.chunk_count}</span>
              </div>
            </div>

            {paper.tags && paper.tags.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center gap-1.5 text-sm text-gray-600 mb-2">
                  <Tag className="w-4 h-4 text-gray-400" />
                  Tags
                </div>
                <div className="flex flex-wrap gap-2">
                  {paper.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Abstract */}
          {paper.abstract && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Abstract</h3>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                {paper.abstract}
              </p>
            </div>
          )}

          {/* File Info */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">Original File</h3>
                <p className="text-sm text-gray-500 mt-1">
                  Uploaded on {new Date(paper.created_at).toLocaleDateString()}
                </p>
              </div>
              <a
                href={`/api/v1/papers/${paper.id}/download`}
                download
                className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </a>
            </div>
          </div>
        </div>

        {/* Right Panel — AI Analysis (40%) */}
        <div className="lg:w-2/5">
          <div className="bg-white rounded-xl border border-gray-200 sticky top-6">
            <div className="border-b border-gray-200 px-4 py-3">
              <h3 className="font-semibold text-gray-900">AI Analysis</h3>
            </div>

            {/* Analysis Tabs */}
            <div className="border-b border-gray-200 px-4">
              <div className="flex gap-1 overflow-x-auto">
                {ANALYSIS_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveAnalysisTab(tab.id)}
                    className={`px-3 py-2 text-xs font-medium whitespace-nowrap border-b-2 transition-colors ${
                      activeAnalysisTab === tab.id
                        ? "border-primary-600 text-primary-600"
                        : "border-transparent text-gray-500 hover:text-gray-700"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Analysis Content */}
            <div className="p-4">
              <AnalysisPanel
                paperId={paper.id}
                analysisType={activeAnalysisTab}
                isProcessed={paper.is_processed}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

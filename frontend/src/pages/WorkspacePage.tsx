import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { workspaceApi } from '../services/workspaceApi';
import { paperApi } from '../services/paperApi';
import { chatApi } from '../services/chatApi';
import { PaperCard } from '../components/PaperCard';
import { UploadPaperModal } from '../components/UploadPaperModal';
import { SynthesisPanel } from '../components/SynthesisPanel';
import type { Workspace, Paper, Conversation } from '../types';
import {
  ArrowLeft, Upload, FileText, MessageSquare, Beaker,
  Search, Loader2, Plus,
} from 'lucide-react';

type TabType = 'papers' | 'conversations' | 'synthesize';

export function WorkspacePage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const navigate = useNavigate();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('papers');
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    if (workspaceId) {
      loadWorkspace();
      loadPapers();
      loadConversations();
    }
  }, [workspaceId]);

  const loadWorkspace = async () => {
    try {
      const ws = await workspaceApi.get(workspaceId!);
      setWorkspace(ws);
    } catch (error) {
      console.error('Failed to load workspace:', error);
      navigate('/dashboard');
    }
  };

  const loadPapers = async () => {
    setIsLoading(true);
    try {
      const response = await paperApi.list(workspaceId!, { search: searchQuery || undefined });
      setPapers(response.items);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadConversations = async () => {
    try {
      const convos = await chatApi.listConversations(workspaceId!);
      setConversations(convos);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const handleDeletePaper = async (paperId: string) => {
    try {
      await paperApi.delete(paperId);
      setPapers((prev) => prev.filter((p) => p.id !== paperId));
    } catch (error) {
      console.error('Failed to delete paper:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const conversation = await chatApi.createConversation(workspaceId!, {
        title: 'New Conversation',
      });
      navigate(`/workspace/${workspaceId}/chat/${conversation.id}`);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const tabs: { id: TabType; label: string; icon: typeof FileText }[] = [
    { id: 'papers', label: 'Papers', icon: FileText },
    { id: 'conversations', label: 'Conversations', icon: MessageSquare },
    { id: 'synthesize', label: 'Synthesize', icon: Beaker },
  ];

  if (!workspace) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </button>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: workspace.color }} />
            <h2 className="font-semibold text-gray-900 truncate">{workspace.name}</h2>
          </div>
          {workspace.description && (
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{workspace.description}</p>
          )}
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-primary-50 text-primary-700 font-medium'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200 text-xs text-gray-500 space-y-1">
          <p>{papers.length} papers</p>
          <p>{conversations.length} conversations</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-auto">
        {activeTab === 'papers' && (
          <>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3 flex-1 max-w-md">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && loadPapers()}
                    placeholder="Search papers..."
                    className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                </div>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              >
                <Upload className="w-4 h-4" />
                Upload Paper
              </button>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
              </div>
            ) : papers.length === 0 ? (
              <div className="text-center py-16">
                <FileText className="w-12 h-12 text-gray-300 mx-auto" />
                <h3 className="mt-3 text-sm font-medium text-gray-900">No papers yet</h3>
                <p className="mt-1 text-sm text-gray-500">Upload your first research paper.</p>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg"
                >
                  <Upload className="w-4 h-4" />
                  Upload Paper
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {papers.map((paper) => (
                  <PaperCard
                    key={paper.id}
                    paper={paper}
                    onClick={() => navigate(`/workspace/${workspaceId}/paper/${paper.id}`)}
                    onDelete={handleDeletePaper}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'conversations' && (
          <>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Conversations</h3>
              <button
                onClick={handleNewConversation}
                className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm font-medium"
              >
                <Plus className="w-4 h-4" />
                New Conversation
              </button>
            </div>

            {conversations.length === 0 ? (
              <div className="text-center py-16">
                <MessageSquare className="w-12 h-12 text-gray-300 mx-auto" />
                <h3 className="mt-3 text-sm font-medium text-gray-900">No conversations yet</h3>
                <p className="mt-1 text-sm text-gray-500">Start a conversation to discuss your papers with AI.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => navigate(`/workspace/${workspaceId}/chat/${conv.id}`)}
                    className="bg-white p-4 rounded-lg border border-gray-200 hover:border-gray-300 cursor-pointer transition-all"
                  >
                    <h4 className="font-medium text-gray-900">{conv.title}</h4>
                    {conv.last_message_preview && (
                      <p className="text-sm text-gray-500 truncate mt-1">{conv.last_message_preview}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                      <span>{conv.message_count} messages</span>
                      <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'synthesize' && (
          <SynthesisPanel workspaceId={workspaceId!} papers={papers} />
        )}
      </main>

      {showUploadModal && (
        <UploadPaperModal
          workspaceId={workspaceId!}
          onClose={() => setShowUploadModal(false)}
          onUploaded={() => {
            setShowUploadModal(false);
            loadPapers();
          }}
        />
      )}
    </div>
  );
}

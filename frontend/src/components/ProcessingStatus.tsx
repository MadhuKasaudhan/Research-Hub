import { useState, useEffect, useRef } from 'react';
import { paperApi } from '../services/paperApi';
import { Check, Loader2, XCircle, FileText, Scissors, Database, Brain, CheckCircle } from 'lucide-react';

interface ProcessingStatusProps {
  paperId: string;
  onComplete: () => void;
}

const STEPS = [
  { key: 'extracting', label: 'Extracting text', icon: FileText },
  { key: 'chunking', label: 'Chunking text', icon: Scissors },
  { key: 'embedding', label: 'Generating embeddings', icon: Database },
  { key: 'analyzing', label: 'Analyzing content', icon: Brain },
  { key: 'completed', label: 'Complete', icon: CheckCircle },
];

const STATUS_ORDER = ['pending', 'extracting', 'chunking', 'embedding', 'analyzing', 'completed'];

export function ProcessingStatus({ paperId, onComplete }: ProcessingStatusProps) {
  const [status, setStatus] = useState<string>('pending');
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    pollStatus();
    intervalRef.current = setInterval(pollStatus, 2000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [paperId]);

  const pollStatus = async () => {
    try {
      const data = await paperApi.getStatus(paperId);
      setStatus(data.processing_status);
      setError(data.processing_error);
      if (data.processing_status === 'completed' || data.processing_status === 'failed') {
        if (intervalRef.current) clearInterval(intervalRef.current);
        if (data.processing_status === 'completed') {
          onComplete();
        }
      }
    } catch (err) {
      console.error('Failed to poll status:', err);
    }
  };

  const getStepState = (stepKey: string): 'completed' | 'active' | 'pending' | 'failed' => {
    if (status === 'failed') {
      const currentIdx = STATUS_ORDER.indexOf(status);
      const stepIdx = STATUS_ORDER.indexOf(stepKey);
      if (stepIdx < currentIdx) return 'completed';
      return 'failed';
    }
    const currentIdx = STATUS_ORDER.indexOf(status);
    const stepIdx = STATUS_ORDER.indexOf(stepKey);
    if (stepIdx < currentIdx) return 'completed';
    if (stepIdx === currentIdx) return 'active';
    return 'pending';
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-semibold text-gray-900 mb-4">Processing Paper</h3>
      <div className="space-y-3">
        {STEPS.map((step) => {
          const state = getStepState(step.key);
          return (
            <div key={step.key} className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                state === 'completed' ? 'bg-green-100' :
                state === 'active' ? 'bg-primary-100' :
                state === 'failed' ? 'bg-red-100' :
                'bg-gray-100'
              }`}>
                {state === 'completed' ? (
                  <Check className="w-4 h-4 text-green-600" />
                ) : state === 'active' ? (
                  <Loader2 className="w-4 h-4 text-primary-600 animate-spin" />
                ) : state === 'failed' ? (
                  <XCircle className="w-4 h-4 text-red-600" />
                ) : (
                  <step.icon className="w-4 h-4 text-gray-400" />
                )}
              </div>
              <span className={`text-sm ${
                state === 'completed' ? 'text-green-700' :
                state === 'active' ? 'text-primary-700 font-medium' :
                state === 'failed' ? 'text-red-700' :
                'text-gray-400'
              }`}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}

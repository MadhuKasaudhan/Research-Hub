import React from 'react';
import { useToastStore, type Toast as ToastItem } from '../store/toastStore';

const typeStyles: Record<string, string> = {
  success: 'bg-green-50 border-green-400 text-green-800',
  error: 'bg-red-50 border-red-400 text-red-800',
  info: 'bg-blue-50 border-blue-400 text-blue-800',
  warning: 'bg-yellow-50 border-yellow-400 text-yellow-800',
};

const typeIcons: Record<string, string> = {
  success: 'M9 12l2 2 4-4',
  error: 'M6 18L18 6M6 6l12 12',
  info: 'M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20 10 10 0 000-20z',
  warning: 'M12 9v2m0 4h.01M12 2a10 10 0 100 20 10 10 0 000-20z',
};

const ToastItem: React.FC<{ toast: ToastItem }> = ({ toast }) => {
  const removeToast = useToastStore((s) => s.removeToast);

  return (
    <div
      className={`flex items-center gap-3 rounded-lg border-l-4 px-4 py-3 shadow-md ${typeStyles[toast.type] || typeStyles.info}`}
      role="alert"
    >
      <svg
        className="h-5 w-5 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d={typeIcons[toast.type] || typeIcons.info}
        />
      </svg>
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => removeToast(toast.id)}
        className="ml-2 flex-shrink-0 opacity-60 hover:opacity-100"
        aria-label="Dismiss"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
};

export const ToastContainer: React.FC = () => {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed inset-0 z-50 flex flex-col items-end gap-2 p-4 sm:p-6">
      <div className="pointer-events-auto flex w-full max-w-sm flex-col gap-2">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} />
        ))}
      </div>
    </div>
  );
};

export default ToastContainer;

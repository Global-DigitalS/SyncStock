import React, { useEffect } from 'react';
import { Loader2, CheckCircle2, XCircle, Circle, X } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { useSyncProgress } from '@/contexts/SyncProgressContext';
import { useWebSocketContext } from '@/contexts/AuthContext';

function SyncOperationCard({ operation, onDismiss }) {
  const { id, title, steps, currentStepIndex, progress, status, message } = operation;

  const getStepIcon = (idx) => {
    if (idx < currentStepIndex) {
      return <CheckCircle2 className="w-4 h-4 text-green-500" />;
    } else if (idx === currentStepIndex && status === 'running') {
      return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
    } else if (status === 'error') {
      return <XCircle className="w-4 h-4 text-red-500" />;
    }
    return <Circle className="w-4 h-4 text-gray-300" />;
  };

  const statusColor = {
    running: 'border-blue-200 bg-blue-50',
    done: 'border-green-200 bg-green-50',
    error: 'border-red-200 bg-red-50',
  }[status];

  const statusBadgeColor = {
    running: 'bg-blue-100 text-blue-800',
    done: 'bg-green-100 text-green-800',
    error: 'bg-red-100 text-red-800',
  }[status];

  const statusBadgeText = {
    running: 'En curso...',
    done: 'Completado',
    error: 'Error',
  }[status];

  return (
    <div className={`border rounded-lg p-4 mb-3 w-80 ${statusColor}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm text-gray-800 flex-1 truncate">{title}</h3>
        <button
          onClick={() => onDismiss(id)}
          className="ml-2 text-gray-400 hover:text-gray-600 p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Steps */}
      <div className="space-y-2 mb-3">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2">
            {getStepIcon(idx)}
            <span className={`text-xs ${
              idx <= currentStepIndex ? 'text-gray-700' : 'text-gray-400'
            }`}>
              {step}
            </span>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      {status === 'running' && (
        <div className="mb-2">
          <Progress value={progress} className="h-1.5" />
          <div className="text-xs text-gray-500 mt-1">{progress}%</div>
        </div>
      )}

      {/* Message */}
      <div className="text-xs text-gray-600 mb-2 break-words max-h-12 overflow-hidden">
        {message}
      </div>

      {/* Status badge */}
      <div className="flex justify-end">
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${statusBadgeColor}`}>
          {statusBadgeText}
        </span>
      </div>
    </div>
  );
}

export default function SyncProgressPanel() {
  const { operations, setProgress, completeSync, failSync, dismissSync } = useSyncProgress();
  const { subscribeWsEvent } = useWebSocketContext();

  // Subscribe to WebSocket events
  useEffect(() => {
    if (!subscribeWsEvent) return;

    const unsubProgress = subscribeWsEvent('sync_progress', (data) => {
      const opId = data.operation_id || data.id;
      setProgress(opId, data.progress || 0, data.message || '');
    });

    const unsubComplete = subscribeWsEvent('sync_complete', (data) => {
      const opId = data.operation_id || data.id;
      completeSync(opId, data.message || 'Completado');
    });

    const unsubError = subscribeWsEvent('sync_error', (data) => {
      const opId = data.operation_id || data.id;
      failSync(opId, data.message || 'Error desconocido');
    });

    return () => {
      if (unsubProgress) unsubProgress();
      if (unsubComplete) unsubComplete();
      if (unsubError) unsubError();
    };
  }, [setProgress, completeSync, failSync, subscribeWsEvent]);

  if (operations.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[9999] max-h-[80vh] overflow-y-auto pointer-events-auto">
      <div className="animate-slide-in">
        {operations.map((op) => (
          <SyncOperationCard
            key={op.id}
            operation={op}
            onDismiss={dismissSync}
          />
        ))}
      </div>
    </div>
  );
}

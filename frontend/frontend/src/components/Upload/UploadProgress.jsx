import React from 'react'
import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function UploadProgress({ filename, uploadPct, status, error }) {
  return (
    <div className="card p-4 fade-in">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-text-primary truncate max-w-xs">{filename}</span>
        {status === 'uploading' && (
          <span className="text-xs text-text-muted">{uploadPct}%</span>
        )}
        {(status === 'pending' || status === 'processing') && (
          <span className="badge badge-processing gap-1">
            <Loader size={10} className="spinner" />
            {status === 'pending' ? 'Queued' : 'Processing'}
          </span>
        )}
        {status === 'completed' && (
          <span className="badge badge-completed gap-1">
            <CheckCircle size={10} />
            Ready
          </span>
        )}
        {status === 'failed' && (
          <span className="badge badge-failed gap-1">
            <XCircle size={10} />
            Failed
          </span>
        )}
      </div>

      {status === 'uploading' && (
        <div className="h-1 bg-surface-2 rounded-full overflow-hidden">
          <div
            className="h-full bg-accent rounded-full transition-all duration-200"
            style={{ width: `${uploadPct}%` }}
          />
        </div>
      )}

      {status === 'processing' && (
        <div className="h-1 bg-surface-2 rounded-full overflow-hidden">
          <div className="h-full bg-accent rounded-full animate-pulse w-3/4" />
        </div>
      )}

      {error && (
        <p className="mt-1 text-xs text-status-failed">{error}</p>
      )}

      {status === 'completed' && (
        <p className="text-xs text-text-muted mt-1">
          Processing complete — open in Library to start chatting
        </p>
      )}
    </div>
  )
}

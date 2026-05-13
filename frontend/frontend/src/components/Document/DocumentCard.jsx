import React from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Music, Video, Trash2, Loader, CheckCircle, XCircle, Clock } from 'lucide-react'

const FILE_ICONS = {
  pdf: FileText,
  audio: Music,
  video: Video,
}

const FILE_COLORS = {
  pdf: 'text-red-400',
  audio: 'text-purple-400',
  video: 'text-blue-400',
}

function StatusBadge({ status }) {
  if (status === 'pending') return (
    <span className="badge badge-pending"><Clock size={10} /> Pending</span>
  )
  if (status === 'processing') return (
    <span className="badge badge-processing"><Loader size={10} className="spinner" /> Processing</span>
  )
  if (status === 'completed') return (
    <span className="badge badge-completed"><CheckCircle size={10} /> Ready</span>
  )
  if (status === 'failed') return (
    <span className="badge badge-failed"><XCircle size={10} /> Failed</span>
  )
  return null
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

export default function DocumentCard({ doc, onDelete }) {
  const navigate = useNavigate()
  const Icon = FILE_ICONS[doc.file_type] || FileText
  const iconColor = FILE_COLORS[doc.file_type] || 'text-text-muted'

  return (
    <div className="card p-4 hover:border-accent/40 transition-colors group fade-in">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-surface-2 rounded-md flex-shrink-0 mt-0.5">
          <Icon size={18} className={iconColor} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary truncate" title={doc.filename}>
            {doc.filename}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-text-muted">{doc.file_size_kb?.toFixed(1)} KB</span>
            <span className="text-text-muted">·</span>
            <span className="text-xs text-text-muted">{formatDate(doc.created_at)}</span>
          </div>
          <div className="mt-2 flex items-center justify-between">
            <StatusBadge status={doc.status} />
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {doc.status === 'completed' && (
                <button
                  onClick={() => navigate(`/documents/${doc.id}`)}
                  className="btn-ghost text-xs py-1 px-2"
                >
                  Open
                </button>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(doc.id) }}
                className="p-1.5 hover:bg-status-failed/10 text-text-muted hover:text-status-failed rounded-md transition-colors"
                title="Delete"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

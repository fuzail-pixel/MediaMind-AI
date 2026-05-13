import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getDocument } from '../services/api'
import SummaryPanel from '../components/Document/SummaryPanel'
import ChatWindow from '../components/Chat/ChatWindow'
import MediaPlayer from '../components/Player/MediaPlayer'
import {
  FileText, Music, Video, ArrowLeft, Loader,
  Clock, HardDrive, Calendar,
} from 'lucide-react'

const FILE_ICONS = { pdf: FileText, audio: Music, video: Video }
const FILE_ICON_COLORS = { pdf: 'text-red-400', audio: 'text-purple-400', video: 'text-blue-400' }

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function formatDuration(sec) {
  if (!sec) return null
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function DocumentView() {
  const { id } = useParams()
  const navigate = useNavigate()
  const playerRef = useRef(null)

  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const res = await getDocument(id)
        setDoc(res.data)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleTimestampPlay = (seconds) => {
    playerRef.current?.seekTo(seconds)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-2 text-text-muted">
        <Loader size={18} className="spinner" />
        <span className="text-sm">Loading document…</span>
      </div>
    )
  }

  if (error || !doc) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-text-muted">
        <p className="text-sm text-status-failed">{error || 'Document not found'}</p>
        <button onClick={() => navigate('/library')} className="btn-secondary text-xs">
          Back to Library
        </button>
      </div>
    )
  }

  const Icon = FILE_ICONS[doc.file_type] || FileText
  const iconColor = FILE_ICON_COLORS[doc.file_type] || 'text-text-muted'
  const isMedia = doc.file_type === 'audio' || doc.file_type === 'video'

  // Build a media source URL — the backend would need to serve the file.
  // Adjust the path below if your backend exposes files at a different route.
  const mediaSrc = isMedia
    ? `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/documents/${id}/file`
    : null

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left panel */}
      <div className="w-80 flex-shrink-0 border-r border-border flex flex-col overflow-y-auto bg-surface-1">
        {/* Back + title */}
        <div className="px-4 py-3 border-b border-border flex-shrink-0">
          <button
            onClick={() => navigate('/library')}
            className="flex items-center gap-1.5 text-xs text-text-muted hover:text-text-primary transition-colors mb-3"
          >
            <ArrowLeft size={12} />
            Library
          </button>
          <div className="flex items-start gap-3">
            <div className="p-2 bg-surface-2 rounded-md flex-shrink-0 mt-0.5">
              <Icon size={16} className={iconColor} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-text-primary leading-snug break-words">
                {doc.filename}
              </p>
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <HardDrive size={10} />
                  {doc.file_size_kb?.toFixed(1)} KB
                </span>
                {doc.duration && (
                  <span className="flex items-center gap-1 text-xs text-text-muted">
                    <Clock size={10} />
                    {formatDuration(doc.duration)}
                  </span>
                )}
                <span className="flex items-center gap-1 text-xs text-text-muted">
                  <Calendar size={10} />
                  {formatDate(doc.created_at)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Media player */}
        {isMedia && (
          <div className="px-3 py-3 border-b border-border flex-shrink-0">
            <MediaPlayer ref={playerRef} fileType={doc.file_type} src={mediaSrc} />
          </div>
        )}

        {/* Summary */}
        <div className="px-3 py-3 flex-1">
          <SummaryPanel documentId={id} initialSummary={doc.summary ? { summary: doc.summary } : null} />
        </div>
      </div>

      {/* Right panel — chat */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {doc.status !== 'completed' ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-text-muted">
            <Loader size={20} className="spinner" />
            <p className="text-sm">Document is still processing…</p>
            <p className="text-xs opacity-60">Come back in a moment</p>
          </div>
        ) : (
          <ChatWindow
            documentId={id}
            fileType={doc.file_type}
            onTimestampPlay={handleTimestampPlay}
          />
        )}
      </div>
    </div>
  )
}

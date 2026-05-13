import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/Upload/UploadZone'
import UploadProgress from '../components/Upload/UploadProgress'
import { uploadFile, getDocument } from '../services/api'
import { ArrowRight } from 'lucide-react'

export default function Home() {
  const navigate = useNavigate()
  const [uploads, setUploads] = useState([]) // { id, filename, uploadPct, status, error }

  const handleUpload = async (file) => {
    const tempId = Date.now().toString()
    const entry = { id: tempId, filename: file.name, uploadPct: 0, status: 'uploading', error: '', docId: null }
    setUploads((prev) => [entry, ...prev])

    let docId = null

    try {
      const res = await uploadFile(file, (pct) => {
        setUploads((prev) =>
          prev.map((u) => (u.id === tempId ? { ...u, uploadPct: pct } : u))
        )
      })
      docId = res.data.document_id

      setUploads((prev) =>
        prev.map((u) =>
          u.id === tempId ? { ...u, status: 'processing', docId } : u
        )
      )

      // Poll for completion
      const interval = setInterval(async () => {
        try {
          const poll = await getDocument(docId)
          const s = poll.data.status
          if (s === 'completed' || s === 'failed') {
            clearInterval(interval)
            setUploads((prev) =>
              prev.map((u) =>
                u.id === tempId
                  ? { ...u, status: s, error: s === 'failed' ? 'Processing failed' : '' }
                  : u
              )
            )
          } else {
            setUploads((prev) =>
              prev.map((u) => (u.id === tempId ? { ...u, status: s } : u))
            )
          }
        } catch {
          clearInterval(interval)
        }
      }, 3000)
    } catch (e) {
      setUploads((prev) =>
        prev.map((u) =>
          u.id === tempId ? { ...u, status: 'failed', error: e.message } : u
        )
      )
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-text-primary">Upload a File</h1>
        <p className="text-sm text-text-muted mt-1">
          PDF documents, audio, or video — up to 50 MB
        </p>
      </div>

      <UploadZone onUpload={handleUpload} />

      {uploads.length > 0 && (
        <div className="mt-6 space-y-2">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium text-text-muted uppercase tracking-wider">Uploads</p>
            {uploads.some((u) => u.status === 'completed') && (
              <button
                onClick={() => navigate('/library')}
                className="flex items-center gap-1 text-xs text-accent hover:text-accent-hover"
              >
                View Library <ArrowRight size={12} />
              </button>
            )}
          </div>
          {uploads.map((u) => (
            <UploadProgress
              key={u.id}
              filename={u.filename}
              uploadPct={u.uploadPct}
              status={u.status}
              error={u.error}
            />
          ))}
        </div>
      )}
    </div>
  )
}

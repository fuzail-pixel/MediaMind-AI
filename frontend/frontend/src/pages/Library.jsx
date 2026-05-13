import React, { useState, useEffect, useCallback } from 'react'
import DocumentList from '../components/Document/DocumentList'
import { listDocuments, deleteDocument } from '../services/api'
import { RefreshCw } from 'lucide-react'

export default function Library() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await listDocuments()
      setDocs(res.data.documents || [])
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this document?')) return
    try {
      await deleteDocument(id)
      setDocs((prev) => prev.filter((d) => d.id !== id))
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-text-primary">Library</h1>
          {!loading && (
            <p className="text-sm text-text-muted mt-0.5">{docs.length} document{docs.length !== 1 ? 's' : ''}</p>
          )}
        </div>
        <button onClick={load} className="btn-ghost flex items-center gap-1.5 text-xs">
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 text-sm text-status-failed bg-status-failed/10 border border-status-failed/20 rounded-md px-4 py-3">
          {error}
        </div>
      )}

      <DocumentList documents={docs} onDelete={handleDelete} loading={loading} />
    </div>
  )
}

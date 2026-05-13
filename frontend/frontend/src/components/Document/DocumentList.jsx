import React from 'react'
import DocumentCard from './DocumentCard'
import { BookOpen } from 'lucide-react'

export default function DocumentList({ documents, onDelete, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="card p-4 animate-pulse">
            <div className="flex gap-3">
              <div className="w-9 h-9 bg-surface-2 rounded-md" />
              <div className="flex-1 space-y-2 pt-1">
                <div className="h-3 bg-surface-2 rounded w-3/4" />
                <div className="h-2 bg-surface-2 rounded w-1/2" />
                <div className="h-4 bg-surface-2 rounded w-1/4 mt-2" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!documents.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-muted">
        <BookOpen size={36} className="mb-3 opacity-40" />
        <p className="text-sm">No documents yet — upload one to get started</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {documents.map((doc) => (
        <DocumentCard key={doc.id} doc={doc} onDelete={onDelete} />
      ))}
    </div>
  )
}

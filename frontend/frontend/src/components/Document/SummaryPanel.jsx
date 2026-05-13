import React, { useState } from 'react'
import { Sparkles, ChevronDown, ChevronUp, Loader } from 'lucide-react'
import { summarizeDocument } from '../../services/api'

export default function SummaryPanel({ documentId, initialSummary }) {
  const [summary, setSummary] = useState(initialSummary || null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState(true)

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await summarizeDocument(documentId)
      setSummary(res.data.summary_data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-surface-2/50 transition-colors"
      >
        <div className="flex items-center gap-2 text-sm font-medium text-text-primary">
          <Sparkles size={14} className="text-accent" />
          Summary
        </div>
        {expanded ? <ChevronUp size={14} className="text-text-muted" /> : <ChevronDown size={14} className="text-text-muted" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-border fade-in">
          {!summary && !loading && (
            <button onClick={handleGenerate} className="btn-secondary mt-3 w-full">
              Generate Summary
            </button>
          )}

          {loading && (
            <div className="flex items-center gap-2 mt-3 text-sm text-text-muted">
              <Loader size={14} className="spinner text-accent" />
              Generating summary…
            </div>
          )}

          {error && (
            <p className="mt-3 text-xs text-status-failed">{error}</p>
          )}

          {summary && (
            <div className="mt-3 space-y-3">
              <p className="text-sm text-text-secondary leading-relaxed">{summary.summary}</p>

              {summary.key_points?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2">Key Points</p>
                  <ul className="space-y-1.5">
                    {summary.key_points.map((pt, i) => (
                      <li key={i} className="flex gap-2 text-sm text-text-secondary">
                        <span className="text-accent mt-0.5 flex-shrink-0">·</span>
                        {pt}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {summary.topics?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {summary.topics.map((t) => (
                    <span key={t} className="px-2 py-0.5 rounded-full bg-surface-2 text-text-secondary text-xs border border-border">
                      {t}
                    </span>
                  ))}
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={loading}
                className="text-xs text-text-muted hover:text-text-secondary transition-colors"
              >
                Regenerate
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

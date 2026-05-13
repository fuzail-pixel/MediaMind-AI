import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Brain, Search, X } from 'lucide-react'
import { searchDocuments } from '../../services/api'

export default function Navbar() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)

  const handleSearch = async (e) => {
    const val = e.target.value
    setQuery(val)
    if (!val.trim()) {
      setResults([])
      setShowResults(false)
      return
    }
    setSearching(true)
    setShowResults(true)
    try {
      const res = await searchDocuments(val)
      setResults(res.data.results || [])
    } catch {
      setResults([])
    } finally {
      setSearching(false)
    }
  }

  const handleResultClick = (docId) => {
    navigate(`/documents/${docId}`)
    setQuery('')
    setResults([])
    setShowResults(false)
  }

  return (
    <header className="bg-surface-1 border-b border-border h-14 flex items-center px-4 gap-4 z-10 flex-shrink-0">
      {/* Logo */}
      <div
        className="flex items-center gap-2 cursor-pointer select-none"
        onClick={() => navigate('/')}
      >
        <Brain size={20} className="text-accent" />
        <span className="font-semibold text-text-primary text-sm tracking-wide">
          MediaMind <span className="text-accent">AI</span>
        </span>
      </div>

      {/* Search */}
      <div className="flex-1 max-w-xl relative">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={query}
            onChange={handleSearch}
            placeholder="Search documents…"
            className="input pl-8 pr-8 h-8 text-xs"
          />
          {query && (
            <button
              onClick={() => { setQuery(''); setResults([]); setShowResults(false) }}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary"
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Dropdown */}
        {showResults && (
          <div className="absolute top-full mt-1 w-full card shadow-xl z-50 overflow-hidden fade-in">
            {searching ? (
              <div className="px-4 py-3 text-xs text-text-muted">Searching…</div>
            ) : results.length === 0 ? (
              <div className="px-4 py-3 text-xs text-text-muted">No results found</div>
            ) : (
              results.map((r) => (
                <button
                  key={r.document_id}
                  onClick={() => handleResultClick(r.document_id)}
                  className="w-full text-left px-4 py-3 hover:bg-surface-2 border-b border-border last:border-0 transition-colors"
                >
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-medium text-text-primary truncate">{r.filename}</span>
                    <span className="text-xs text-text-muted ml-2 flex-shrink-0">
                      {(r.similarity * 100).toFixed(0)}% match
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary line-clamp-1">{r.excerpt}</p>
                </button>
              ))
            )}
          </div>
        )}
      </div>
    </header>
  )
}

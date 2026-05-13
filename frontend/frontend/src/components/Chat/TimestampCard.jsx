import React from 'react'
import { Play } from 'lucide-react'

export default function TimestampCard({ ts, onPlay }) {
  return (
    <div className="flex items-start gap-2 bg-surface-2 border border-border rounded-md px-3 py-2 mt-1 group hover:border-accent/40 transition-colors">
      <button
        onClick={() => onPlay(ts.start)}
        className="flex-shrink-0 flex items-center gap-1 text-accent hover:text-accent-hover text-xs font-mono font-medium mt-0.5"
        title="Play from here"
      >
        <Play size={10} fill="currentColor" />
        {ts.timestamp_formatted || formatTime(ts.start)}
      </button>
      <p className="text-xs text-text-secondary leading-relaxed flex-1 line-clamp-2">{ts.text}</p>
    </div>
  )
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return [h > 0 ? h : null, String(m).padStart(2, '0'), String(s).padStart(2, '0')]
    .filter(Boolean)
    .join(':')
}

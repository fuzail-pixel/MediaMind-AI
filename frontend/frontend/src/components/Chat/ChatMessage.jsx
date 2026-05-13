import React from 'react'
import { Brain } from 'lucide-react'
import TimestampCard from './TimestampCard'

export default function ChatMessage({ msg, onTimestampPlay }) {
  const isUser = msg.role === 'user'

  return (
    <div className={`flex gap-3 fade-in ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-accent/15 flex items-center justify-center flex-shrink-0 mt-1">
          <Brain size={13} className="text-accent" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div
          className={`rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${
            isUser
              ? 'bg-accent text-white rounded-tr-sm'
              : 'bg-surface-1 border border-border text-text-primary rounded-tl-sm'
          }`}
        >
          {msg.content}
        </div>

        {/* Confidence + timestamps for assistant */}
        {!isUser && (
          <div className="w-full">
            {msg.confidence != null && (
              <span className="text-xs text-text-muted">
                {(msg.confidence * 100).toFixed(0)}% confidence
              </span>
            )}
            {msg.timestamps?.length > 0 && (
              <div className="mt-1 space-y-1">
                {msg.timestamps.map((ts, i) => (
                  <TimestampCard key={i} ts={ts} onPlay={onTimestampPlay} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

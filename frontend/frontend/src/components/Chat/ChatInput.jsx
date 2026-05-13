import React, { useState, useRef } from 'react'
import { Send, Loader } from 'lucide-react'

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('')
  const textareaRef = useRef(null)

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e) => {
    setValue(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }

  return (
    <div className="border-t border-border bg-surface-1 p-3">
      <div className="flex items-end gap-2 bg-surface-2 border border-border rounded-lg px-3 py-2 focus-within:border-accent/60 transition-colors">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question…"
          rows={1}
          disabled={disabled}
          className="flex-1 bg-transparent text-sm text-text-primary placeholder-text-muted resize-none focus:outline-none leading-relaxed disabled:opacity-50"
          style={{ minHeight: '24px', maxHeight: '120px' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-md bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors mb-0.5"
        >
          {disabled ? (
            <Loader size={13} className="spinner text-white" />
          ) : (
            <Send size={13} className="text-white" />
          )}
        </button>
      </div>
      <p className="text-xs text-text-muted mt-1.5 text-center">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}

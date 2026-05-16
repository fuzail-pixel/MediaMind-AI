import React, { useState, useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { getChatHistory, streamAnswer } from '../../services/api'
import { MessageSquare, Loader } from 'lucide-react'
import { authService } from '../../services/auth'

const STREAM_URL = `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/chat/stream`

export default function ChatWindow({ documentId, fileType, onTimestampPlay }) {
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [streaming, setStreaming] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    const load = async () => {
      setLoadingHistory(true)
      try {
        const res = await getChatHistory(documentId)
        const sessions = res.data.sessions || []
        if (sessions.length > 0) {
          const latest = sessions[sessions.length - 1]
          setSessionId(latest.session_id)
          setMessages(
            latest.messages.map((m) => ({
              role: m.role,
              content: m.content,
              confidence: m.confidence,
              timestamps: m.timestamps,
            }))
          )
        }
      } catch {
        // No history yet
      } finally {
        setLoadingHistory(false)
      }
    }
    load()
  }, [documentId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text) => {
    setError('')
    setStreaming(true)

    // Add user message immediately
    setMessages((prev) => [...prev, { role: 'user', content: text }])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      const payload = { document_id: documentId, question: text }
      if (sessionId) payload.session_id = sessionId

      // CORRECT — Authorization inside headers object
      const response = await fetch(STREAM_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authService.getToken()}`  // ← inside headers
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let assistantAdded = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data:')) continue
          const jsonStr = trimmed.slice(5).trim()
          if (!jsonStr) continue

          let event
          try { event = JSON.parse(jsonStr) } catch { continue }

          if (event.type === 'session') {
            if (!sessionId) setSessionId(event.session_id)

          } else if (event.type === 'token') {
            if (!assistantAdded) {
              // Add assistant message on the FIRST token, not before
              // This prevents the overlap between thinking dots and streaming message
              setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: event.content, confidence: null, timestamps: [], streaming: true },
              ])
              assistantAdded = true
            } else {
              setMessages((prev) => {
                const updated = [...prev]
                const last = { ...updated[updated.length - 1] }
                last.content += event.content
                updated[updated.length - 1] = last
                return updated
              })
            }

          } else if (event.type === 'done') {
            if (!assistantAdded) {
              // Edge case: done fired with no tokens (empty answer)
              setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: event.full_answer || '', confidence: null, timestamps: [], streaming: false },
              ])
            } else {
              setMessages((prev) => {
                const updated = [...prev]
                const last = { ...updated[updated.length - 1] }
                last.content = event.full_answer || last.content
                last.streaming = false
                updated[updated.length - 1] = last
                return updated
              })
            }
          }
        }
      }
    } catch (e) {
      if (e.name === 'AbortError') return
      setError(e.message)
      // Remove assistant message if it was added
      setMessages((prev) => {
        const updated = [...prev]
        if (updated[updated.length - 1]?.role === 'assistant') updated.pop()
        return updated
      })
    } finally {
      setStreaming(false)
      abortRef.current = null
    }
  }

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border flex-shrink-0">
        <MessageSquare size={14} className="text-accent" />
        <span className="text-sm font-medium text-text-primary">Chat</span>
        {streaming && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-accent">
            <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
            Streaming
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {loadingHistory ? (
          <div className="flex items-center justify-center h-full text-text-muted gap-2">
            <Loader size={14} className="spinner" />
            <span className="text-sm">Loading history…</span>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-muted text-center px-6">
            <MessageSquare size={28} className="mb-3 opacity-30" />
            <p className="text-sm">Ask anything about this document</p>
            <p className="text-xs mt-1 opacity-60">
              {fileType === 'pdf'
                ? 'Try: "What is the main topic?" or "Summarize section 2"'
                : 'Try: "What was discussed at 2 minutes?" or "Find mentions of X"'}
            </p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <ChatMessage key={i} msg={msg} onTimestampPlay={onTimestampPlay} />
          ))
        )}

        {/* Thinking dots — shown only while streaming and no assistant message yet */}
        {streaming && (messages.length === 0 || messages[messages.length - 1]?.role === 'user') && (
          <div className="flex gap-3 fade-in">
            <div className="w-7 h-7 rounded-full bg-accent/15 flex items-center justify-center flex-shrink-0">
              <Loader size={13} className="text-accent spinner" />
            </div>
            <div className="bg-surface-1 border border-border rounded-lg rounded-tl-sm px-3.5 py-2.5">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="text-xs text-status-failed bg-status-failed/10 border border-status-failed/20 rounded-md px-3 py-2 fade-in">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={handleSend} disabled={streaming} />
    </div>
  )
}
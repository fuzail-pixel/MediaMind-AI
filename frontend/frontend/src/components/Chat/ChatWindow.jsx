import React, { useState, useEffect, useRef } from 'react'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'
import { askQuestion, getChatHistory } from '../../services/api'
import { MessageSquare, Loader } from 'lucide-react'

export default function ChatWindow({ documentId, fileType, onTimestampPlay }) {
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [sending, setSending] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(true)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)

  // Load chat history on mount
  useEffect(() => {
    const load = async () => {
      setLoadingHistory(true)
      try {
        const res = await getChatHistory(documentId)
        const sessions = res.data.sessions || []
        if (sessions.length > 0) {
          const latest = sessions[sessions.length - 1]
          setSessionId(latest.session_id)
          const msgs = []
          for (const m of latest.messages) {
            msgs.push({
              role: m.role,
              content: m.content,
              confidence: m.confidence,
              timestamps: m.timestamps,
            })
          }
          setMessages(msgs)
        }
      } catch {
        // Fresh start — no history
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
    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setSending(true)
    setError('')

    try {
      const payload = { document_id: documentId, question: text }
      if (sessionId) payload.session_id = sessionId

      const res = await askQuestion(payload)
      const d = res.data

      if (!sessionId) setSessionId(d.session_id)

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: d.answer,
          confidence: d.confidence,
          timestamps: d.timestamps || [],
        },
      ])
    } catch (e) {
      setError(e.message)
      setMessages((prev) => prev.slice(0, -1)) // remove optimistic user msg
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border flex-shrink-0">
        <MessageSquare size={14} className="text-accent" />
        <span className="text-sm font-medium text-text-primary">Chat</span>
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
            <ChatMessage
              key={i}
              msg={msg}
              onTimestampPlay={onTimestampPlay}
            />
          ))
        )}

        {sending && (
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
          <div className="text-xs text-status-failed bg-status-failed/10 border border-status-failed/20 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={sending} />
    </div>
  )
}

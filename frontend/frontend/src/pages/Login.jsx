import { Brain } from 'lucide-react'
import { authService } from '../services/auth'

export default function Login() {
  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="card p-10 text-center max-w-md w-full shadow-2xl">

        <div className="flex items-center justify-center gap-2 mb-6">
          <Brain size={36} className="text-accent" />
          <h1 className="text-2xl font-semibold text-text-primary">
            MediaMind <span className="text-accent">AI</span>
          </h1>
        </div>

        <p className="text-text-secondary mb-8">
          AI-powered Document & Multimedia Q&A
        </p>

        <div className="text-left mb-8 space-y-2">
          {[
            '📄 Upload PDFs and ask questions',
            '🎙️ Transcribe audio with timestamps',
            '🎬 Query video content intelligently',
            '⚡ Real-time streaming responses',
            '🔍 Semantic search across documents',
          ].map((f, i) => (
            <p key={i} className="text-sm text-text-secondary">{f}</p>
          ))}
        </div>

        <button
          onClick={authService.login}
          className="w-full flex items-center justify-center gap-3 bg-white text-gray-800 font-semibold py-3 px-6 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
          Continue with Google
        </button>

        <p className="text-text-muted text-xs mt-4">Your data is private and secure</p>
      </div>
    </div>
  )
}
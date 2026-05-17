import { Brain, Upload, MessageCircle, Zap, FileText, Mic, Video, Search, Lock, UserCircle, Clock, Trash2, Shield, EyeOff, Rocket } from 'lucide-react'
import { authService } from '../services/auth'

export default function Login() {
  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="min-h-screen bg-surface font-sans">

      {/* Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent/15 flex items-center justify-center">
            <Brain size={16} className="text-accent" />
          </div>
          <span className="text-sm font-semibold text-text-primary">
            MediaMind <span className="text-accent">AI</span>
          </span>
        </div>
        <button
          onClick={() => scrollTo('login-section')}
          className="btn-secondary flex items-center gap-2 text-xs"
        >
          Sign in
        </button>
      </nav>

      {/* Hero */}
      <section className="px-8 py-14 text-center border-b border-border">
        <div className="inline-flex items-center gap-2 bg-accent/10 text-accent text-xs font-medium px-3 py-1.5 rounded-full mb-5">
          ✦ Powered by Gemini + Whisper
        </div>
        <h1 className="text-3xl font-semibold text-text-primary leading-tight mb-3">
          Chat with your documents,<br />
          <span className="text-accent">audio, and video files</span>
        </h1>
        <p className="text-sm text-text-secondary leading-relaxed max-w-md mx-auto mb-7">
          Upload any file and ask questions in plain English. Get instant AI answers with timestamps, summaries, and clickable media clips — all streaming in real time.
        </p>
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => scrollTo('login-section')} className="btn-primary flex items-center gap-2 text-sm">
            <Rocket size={14} /> Get started free
          </button>
          <button onClick={() => scrollTo('how-it-works')} className="btn-secondary flex items-center gap-2 text-sm">
            See how it works
          </button>
        </div>

        {/* Mock chat */}
        <div className="mt-8 max-w-md mx-auto card p-4 text-left">
          <div className="flex gap-1.5 mb-3">
            <div className="w-2.5 h-2.5 rounded-full bg-status-failed" />
            <div className="w-2.5 h-2.5 rounded-full bg-status-pending" />
            <div className="w-2.5 h-2.5 rounded-full bg-status-completed" />
          </div>
          <div className="flex flex-col gap-2">
            <div className="self-end bg-accent text-white text-xs px-3 py-2 rounded-lg rounded-tr-sm max-w-xs">
              What did the speaker say about climate at minute 4?
            </div>
            <div className="self-start bg-surface-2 border border-border text-text-primary text-xs px-3 py-2 rounded-lg rounded-tl-sm max-w-sm">
              At around 4 minutes, the speaker argues that carbon capture alone is insufficient — renewable adoption must accelerate in parallel.
              <div className="mt-1.5">
                <span className="inline-flex items-center gap-1 bg-accent/10 text-accent text-xs px-2 py-0.5 rounded-md">
                  ▶ 00:04:12 — Jump to clip
                </span>
              </div>
            </div>
            <div className="self-end bg-accent text-white text-xs px-3 py-2 rounded-lg rounded-tr-sm max-w-xs">
              Summarise the three key recommendations
            </div>
            <div className="self-start flex gap-1 px-3 py-2 bg-surface-2 border border-border rounded-lg rounded-tl-sm">
              {[0,1,2].map(i => (
                <span key={i} className="w-1.5 h-1.5 rounded-full bg-text-muted animate-bounce" style={{animationDelay:`${i*0.15}s`}} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-8 py-10 border-b border-border" id="how-it-works">
        <p className="text-xs font-medium text-accent uppercase tracking-widest mb-1.5">How it works</p>
        <p className="text-lg font-semibold text-text-primary mb-6">Three steps to insights</p>
        <div className="grid grid-cols-3 divide-x divide-border border border-border rounded-lg overflow-hidden">
          {[
            { icon: Upload, title: 'Upload your file', desc: 'PDF, MP3, MP4, WAV or MOV up to 50 MB. Processed automatically in the background.' },
            { icon: MessageCircle, title: 'Ask anything', desc: 'Type questions in plain English. Semantic search — not just keyword matching.' },
            { icon: Zap, title: 'Get instant answers', desc: 'Responses stream word by word. Jump to exact video timestamps with one click.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="p-5">
              <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center mb-3">
                <Icon size={15} className="text-accent" />
              </div>
              <h3 className="text-xs font-medium text-text-primary mb-1.5">{title}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-8 py-10 border-b border-border">
        <p className="text-xs font-medium text-accent uppercase tracking-widest mb-1.5">Features</p>
        <p className="text-lg font-semibold text-text-primary mb-5">Everything you need</p>
        <div className="grid grid-cols-2 gap-3">
          {[
            { icon: FileText, color: 'bg-blue-900/30 text-blue-400', title: 'PDF question answering', desc: 'Upload contracts, reports, or research papers. Ask specific questions and get cited excerpts instantly.' },
            { icon: Mic, color: 'bg-teal-900/30 text-teal-400', title: 'Audio transcription + Q&A', desc: 'Whisper auto-transcribes recordings. Ask what was discussed at any point and jump there.' },
            { icon: Video, color: 'bg-amber-900/30 text-amber-400', title: 'Video timestamp navigation', desc: 'Find the exact moment a topic is discussed. Click play and the player seeks right to it.' },
            { icon: Search, color: 'bg-purple-900/30 text-purple-400', title: 'Semantic search', desc: 'Search across all your files by meaning, not keywords. Powered by pgvector embeddings.' },
          ].map(({ icon: Icon, color, title, desc }) => (
            <div key={title} className="card p-4">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center mb-3 ${color}`}>
                <Icon size={14} />
              </div>
              <h3 className="text-xs font-medium text-text-primary mb-1.5">{title}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Login */}
      <section className="px-8 py-12 bg-surface-1" id="login-section">
        <div className="grid grid-cols-2 gap-14 max-w-3xl mx-auto items-center">
          <div>
            <h2 className="text-xl font-semibold text-text-primary mb-3">Ready to get started?</h2>
            <p className="text-sm text-text-secondary leading-relaxed mb-5">
              Sign in with Google — takes less than 10 seconds. Your files are private and only visible to you.
            </p>
            <div className="flex flex-col gap-3">
              {[
                { icon: Lock, text: 'Secure Google OAuth — no passwords stored' },
                { icon: UserCircle, text: 'Your documents are private to your account' },
                { icon: Clock, text: 'Session lasts 7 days' },
                { icon: Trash2, text: 'Delete any file at any time' },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-3 text-xs text-text-secondary">
                  <Icon size={13} className="text-accent flex-shrink-0" />
                  {text}
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6 flex flex-col gap-4">
            <div className="text-center">
              <p className="text-sm font-medium text-text-primary mb-1">Sign in to MediaMind AI</p>
              <span className="text-xs text-text-muted">One account, all your documents</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xs text-text-muted">continue with</span>
              <div className="flex-1 h-px bg-border" />
            </div>
            <button
              onClick={authService.login}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-800 font-medium py-2.5 px-4 rounded-lg border border-gray-200 transition-colors text-sm"
            >
              <svg width="16" height="16" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Sign in with Google
            </button>
            <div className="flex justify-center gap-4">
              {[{ icon: Shield, label: 'Secure' }, { icon: EyeOff, label: 'Private' }].map(({ icon: Icon, label }) => (
                <span key={label} className="flex items-center gap-1.5 text-xs text-text-muted">
                  <Icon size={11} /> {label}
                </span>
              ))}
            </div>
            <p className="text-xs text-text-muted text-center leading-relaxed">
              By signing in you agree to use this application responsibly. Your files are only accessible to you.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-4 border-t border-border text-center">
        <p className="text-xs text-text-muted">© 2026 MediaMind AI. All rights reserved.</p>
      </footer>

    </div>
  )
}
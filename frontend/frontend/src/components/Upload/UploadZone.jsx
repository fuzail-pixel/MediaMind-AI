import React, { useRef, useState } from 'react'
import { UploadCloud, FileText, Music, Video } from 'lucide-react'

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'audio/x-m4a': ['.m4a'],
  'audio/mp4': ['.m4a'],
  'video/mp4': ['.mp4'],
  'video/x-msvideo': ['.avi'],
  'video/quicktime': ['.mov'],
  'video/x-matroska': ['.mkv'],
}

const ALL_EXTS = Object.values(ACCEPTED).flat().join(', ')

function getFileIcon(file) {
  if (file.type === 'application/pdf') return FileText
  if (file.type.startsWith('audio/')) return Music
  if (file.type.startsWith('video/')) return Video
  return FileText
}

export default function UploadZone({ onUpload, disabled }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')

  const validate = (file) => {
    if (!file) return 'No file selected'
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    const allExts = Object.values(ACCEPTED).flat()
    if (!allExts.includes(ext)) return `Unsupported file type: ${ext}`
    if (file.size > 50 * 1024 * 1024) return 'File exceeds 50 MB limit'
    return null
  }

  const handleFile = (file) => {
    const err = validate(file)
    if (err) { setError(err); setSelected(null); return }
    setError('')
    setSelected(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleChange = (e) => handleFile(e.target.files[0])

  const handleUpload = () => {
    if (selected) onUpload(selected)
  }

  const Icon = selected ? getFileIcon(selected) : UploadCloud

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-lg p-10 flex flex-col items-center gap-3 cursor-pointer transition-colors select-none
          ${dragging ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/50 hover:bg-surface-2/50'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <Icon
          size={36}
          className={dragging ? 'text-accent' : 'text-text-muted'}
        />
        {selected ? (
          <>
            <p className="text-sm font-medium text-text-primary">{selected.name}</p>
            <p className="text-xs text-text-muted">
              {(selected.size / 1024).toFixed(1)} KB — click to change
            </p>
          </>
        ) : (
          <>
            <p className="text-sm font-medium text-text-primary">
              Drop a file here, or click to browse
            </p>
            <p className="text-xs text-text-muted">PDF, MP3, WAV, M4A, MP4, AVI, MOV, MKV · max 50 MB</p>
          </>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ALL_EXTS}
        onChange={handleChange}
        className="hidden"
      />

      {error && (
        <p className="mt-2 text-xs text-status-failed">{error}</p>
      )}

      {selected && !error && (
        <div className="mt-3 flex justify-end">
          <button
            onClick={handleUpload}
            disabled={disabled}
            className="btn-primary"
          >
            Upload
          </button>
        </div>
      )}
    </div>
  )
}

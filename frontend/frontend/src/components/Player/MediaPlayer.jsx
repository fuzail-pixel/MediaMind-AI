import React, { useRef, forwardRef, useImperativeHandle } from 'react'

const MediaPlayer = forwardRef(function MediaPlayer({ fileType, src }, ref) {
  const mediaRef = useRef(null)

  useImperativeHandle(ref, () => ({
    seekTo: (seconds) => {
      if (mediaRef.current) {
        mediaRef.current.currentTime = seconds
        mediaRef.current.play()
      }
    },
  }))

  if (!src) return null

  return (
    <div className="card p-3">
      {fileType === 'audio' ? (
        <audio
          ref={mediaRef}
          src={src}
          controls
          className="w-full h-10"
          style={{ colorScheme: 'dark' }}
        />
      ) : (
        <video
          ref={mediaRef}
          src={src}
          controls
          className="w-full rounded-md max-h-52 bg-black"
        />
      )}
    </div>
  )
})

export default MediaPlayer

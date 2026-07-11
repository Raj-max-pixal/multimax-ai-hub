import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Play, RotateCcw, Volume2 } from 'lucide-react'
import { useToast } from '../contexts/ToastContext'

export default function VoiceAssistant() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [transcript, setTranscript] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const { addToast } = useToast()

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())
        setIsProcessing(true)
        
        await new Promise(resolve => setTimeout(resolve, 1500))
        
        setTranscript('This is a sample transcript. Speech-to-text functionality will connect to your backend service.')
        setIsProcessing(false)
      }

      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      
      timerRef.current = window.setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      addToast('Could not access microphone', 'error')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }

  const clearTranscript = () => {
    setTranscript('')
    setRecordingTime(0)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0')
    const secs = (seconds % 60).toString().padStart(2, '0')
    return `${mins}:${secs}`
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 mb-2">
          Voice Assistant
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Speak naturally and let AI transcribe your voice
        </p>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 mb-6">
        {/* Recording Visualizer */}
        <div className="flex flex-col items-center mb-8">
          <div className="relative mb-6">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
              className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${
                isRecording
                  ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                  : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'
              } disabled:opacity-50`}
            >
              {isRecording ? (
                <Square className="w-10 h-10 text-white" />
              ) : (
                <Mic className="w-10 h-10 text-white" />
              )}
            </button>
            {isRecording && (
              <>
                <div className="absolute inset-0 w-24 h-24 rounded-full bg-red-500/20 animate-ping" />
              </>
            )}
          </div>

          <div className="text-4xl font-mono font-bold text-slate-800 dark:text-slate-100">
            {formatTime(recordingTime)}
          </div>

          <p className="text-slate-500 dark:text-slate-400 mt-2">
            {isRecording ? 'Recording...' : isProcessing ? 'Processing...' : 'Tap to start'}
          </p>
        </div>

        {/* Actions */}
        {transcript && !isRecording && !isProcessing && (
          <div className="flex items-center justify-center gap-4 mb-8">
            <button
              onClick={clearTranscript}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-all"
            >
              <RotateCcw className="w-5 h-5" />
              Clear
            </button>
            <button
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-all"
            >
              <Play className="w-5 h-5" />
              Play
            </button>
          </div>
        )}

        {/* Transcript */}
        {transcript && (
          <div className="p-6 bg-slate-100 dark:bg-slate-800 rounded-xl">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-500/10 rounded-lg">
                <Volume2 className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-slate-800 dark:text-slate-100 mb-2">
                  Transcript
                </h4>
                <p className="text-slate-600 dark:text-slate-300">
                  {transcript}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Tips */}
      <div className="bg-gradient-to-br from-orange-500/10 to-yellow-500/10 border border-orange-500/20 rounded-2xl p-6">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3">
          Tips for better results
        </h3>
        <ul className="space-y-2 text-slate-600 dark:text-slate-300">
          <li className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full" />
            Speak clearly and at a normal pace
          </li>
          <li className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full" />
            Reduce background noise
          </li>
          <li className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 bg-orange-500 rounded-full" />
            Keep your microphone at a consistent distance
          </li>
        </ul>
      </div>
    </div>
  )
}

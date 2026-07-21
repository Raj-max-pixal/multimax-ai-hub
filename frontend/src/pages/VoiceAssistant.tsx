import { useEffect, useRef, useState } from 'react'
import { Bot, Copy, Mic, Play, RotateCcw, Send, Square, Volume2 } from 'lucide-react'
import { getOllamaModels, transcribeAudio, voiceChat } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function VoiceAssistant() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [answer, setAnswer] = useState('')
  const [model, setModel] = useState('qwen3:4b')
  const [models, setModels] = useState<{ name: string }[]>([{ name: 'qwen3:4b' }, { name: 'phi3:latest' }])
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const { addToast } = useToast()

  useEffect(() => {
    getOllamaModels().then(data => data.models?.length && setModels(data.models)).catch(() => undefined)
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      mediaRecorder.ondataavailable = (e) => e.data.size > 0 && audioChunksRef.current.push(e.data)
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop())
        setIsProcessing(true)
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
          const data = await transcribeAudio(audioBlob)
          const text = data.transcript || ''
          setTranscript(text)
          if (text) await askVoice(text)
        } catch (error: any) {
          addToast(error.message || 'Transcription failed', 'error')
        } finally {
          setIsProcessing(false)
        }
      }
      mediaRecorder.start()
      setIsRecording(true)
      setRecordingTime(0)
      timerRef.current = window.setInterval(() => setRecordingTime(prev => prev + 1), 1000)
    } catch {
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

  const askVoice = async (text = transcript) => {
    if (!text.trim()) return addToast('Add transcript text first', 'error')
    setIsProcessing(true)
    try {
      const data = await voiceChat({ transcript: text, model })
      setAnswer(data.answer || '')
      speak(data.answer || '')
    } catch (error: any) {
      addToast(error.message || 'Voice assistant failed', 'error')
      setAnswer(`Error: ${error.message || 'Voice assistant failed'}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const speak = (text: string) => {
    if (!text || !('speechSynthesis' in window)) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text.replace(/```[\s\S]*?```/g, 'code block omitted'))
    utterance.rate = 1
    window.speechSynthesis.speak(utterance)
  }

  const clearAll = () => {
    setTranscript('')
    setAnswer('')
    setRecordingTime(0)
    window.speechSynthesis?.cancel()
  }

  const copy = async () => {
    await navigator.clipboard.writeText(`Transcript:\n${transcript}\n\nAnswer:\n${answer}`)
    addToast('Copied', 'success')
  }

  const formatTime = (seconds: number) => `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Voice Assistant</h1><p className="text-slate-500 dark:text-slate-400">Phase 7: speech-to-text, voice AI reply, and browser text-to-speech.</p></div>
        <select value={model} onChange={(e) => setModel(e.target.value)} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200">{models.map(m => <option key={m.name}>{m.name}</option>)}</select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8">
          <div className="flex flex-col items-center mb-8">
            <button onClick={isRecording ? stopRecording : startRecording} disabled={isProcessing} className={`w-24 h-24 rounded-full flex items-center justify-center transition-all ${isRecording ? 'bg-red-500 hover:bg-red-600 animate-pulse' : 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'} disabled:opacity-50`}>
              {isRecording ? <Square className="w-10 h-10 text-white" /> : <Mic className="w-10 h-10 text-white" />}
            </button>
            <div className="mt-6 text-4xl font-mono font-bold text-slate-800 dark:text-slate-100">{formatTime(recordingTime)}</div>
            <p className="text-slate-500 dark:text-slate-400 mt-2">{isRecording ? 'Recording...' : isProcessing ? 'Processing...' : 'Tap to start'}</p>
          </div>
          <textarea value={transcript} onChange={(e) => setTranscript(e.target.value)} rows={8} placeholder="Transcript appears here. You can also type and send..." className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <div className="mt-4 flex flex-wrap gap-3"><button onClick={() => askVoice()} disabled={isProcessing || !transcript.trim()} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-4 py-2 font-semibold text-white disabled:opacity-50"><Send className="w-4 h-4" />Ask AI</button><button onClick={() => speak(answer)} disabled={!answer} className="inline-flex items-center gap-2 rounded-xl bg-blue-500 px-4 py-2 font-semibold text-white disabled:opacity-50"><Play className="w-4 h-4" />Speak</button><button onClick={copy} disabled={!answer && !transcript} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200 disabled:opacity-50"><Copy className="w-4 h-4" /></button><button onClick={clearAll} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200"><RotateCcw className="w-4 h-4" /></button></div>
        </div>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-4"><div className="p-2 bg-green-500/10 rounded-lg"><Bot className="w-5 h-5 text-green-600 dark:text-green-400" /></div><h2 className="font-semibold text-slate-800 dark:text-slate-100">AI Voice Reply</h2></div>
          <div className="min-h-[360px] rounded-xl bg-slate-100 dark:bg-slate-800 p-5 text-slate-700 dark:text-slate-200 whitespace-pre-wrap">{answer || 'AI spoken response will appear here.'}</div>
          <div className="mt-6 bg-gradient-to-br from-orange-500/10 to-yellow-500/10 border border-orange-500/20 rounded-2xl p-5"><div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100 mb-2"><Volume2 className="w-5 h-5" />Voice notes</div><p className="text-sm text-slate-600 dark:text-slate-300">Backend transcription is currently a local stub unless you connect Whisper. Browser speech synthesis is used for free text-to-speech.</p></div>
        </div>
      </div>
    </div>
  )
}

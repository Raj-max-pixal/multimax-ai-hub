import { useEffect, useState } from 'react'
import { Copy, Film, Play } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { generateVideo, getOllamaModels } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function VideoStudio() {
  const [prompt, setPrompt] = useState('Create a 30 second launch video for Multimax AI Hub showing chat, coding, research, agents, and automation.')
  const [style, setStyle] = useState('shorts')
  const [duration, setDuration] = useState(30)
  const [model, setModel] = useState('qwen3:4b')
  const [models, setModels] = useState<{ name: string }[]>([{ name: 'qwen3:4b' }, { name: 'phi3:latest' }])
  const [loading, setLoading] = useState(false)
  const [plan, setPlan] = useState('')
  const [frames, setFrames] = useState<string[]>([])
  const { addToast } = useToast()

  useEffect(() => { getOllamaModels().then(data => data.models?.length && setModels(data.models)).catch(() => undefined) }, [])

  const generate = async () => {
    if (!prompt.trim()) return addToast('Enter a video idea first', 'error')
    setLoading(true)
    try {
      const data = await generateVideo({ prompt, style, duration_seconds: duration, model })
      setPlan(data.plan || '')
      setFrames(data.frames || [])
    } catch (e: any) {
      addToast(e.message || 'Video generation failed', 'error')
      setPlan(`Error: ${e.message || 'Video generation failed'}`)
    } finally {
      setLoading(false)
    }
  }

  const copy = async () => { await navigator.clipboard.writeText(plan); addToast('Copied', 'success') }

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Video Studio</h1><p className="text-slate-500 dark:text-slate-400">Phase 9: AI video storyboard, scene frames, narration, subtitles, and export planning.</p></div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Film className="w-5 h-5 text-green-500" /> Generate Video Plan</div>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={8} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100" />
          <select value={style} onChange={(e) => setStyle(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['shorts','explainer','ad','tutorial','story'].map(x => <option key={x}>{x}</option>)}</select>
          <select value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{[15,30,60,90,180].map(x => <option key={x} value={x}>{x}s</option>)}</select>
          <select value={model} onChange={(e) => setModel(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{models.map(m => <option key={m.name}>{m.name}</option>)}</select>
          <button onClick={generate} disabled={loading} className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-green-500 px-5 py-3 font-semibold text-white hover:bg-green-600 disabled:opacity-60"><Play className="w-4 h-4" />{loading ? 'Generating...' : 'Generate Video Plan'}</button>
          <p className="text-xs text-slate-500">This phase generates a production-ready storyboard and local concept frames. Full video rendering can later connect to open-source video models.</p>
        </div>
        <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex items-center justify-between mb-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100">Storyboard</h2><button onClick={copy} disabled={!plan} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40"><Copy className="w-4 h-4" /></button></div>
          {frames.length > 0 && <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-5">{frames.map((frame, index) => <div key={index} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-2"><img src={frame} alt={`Scene ${index + 1}`} className="rounded-lg w-full" /><p className="mt-2 text-xs text-slate-500">Scene {index + 1}</p></div>)}</div>}
          <div className="prose prose-slate dark:prose-invert max-w-none rounded-xl bg-slate-100 dark:bg-slate-800 p-5"><ReactMarkdown remarkPlugins={[remarkGfm]}>{plan || (loading ? 'Creating video storyboard...' : 'Generated video plan appears here.')}</ReactMarkdown></div>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { BookOpen, Copy, FileSearch, Globe2, Newspaper, Search, ShieldCheck, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getOllamaModels, runResearchSearch, type ResearchMode } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { useAuth } from '../contexts/AuthContext'
import { cn } from '../lib/utils'

type ResearchSource = {
  title: string
  url: string
  snippet: string
}

type ResearchRun = {
  id: string
  query: string
  mode: ResearchMode
  model: string
  summary: string
  sources: ResearchSource[]
  createdAt: string
}

const modes: { id: ResearchMode; label: string; icon: any; description: string }[] = [
  { id: 'web', label: 'Web Search', icon: Globe2, description: 'Fast answer with cited web sources.' },
  { id: 'deep', label: 'Deep Search', icon: FileSearch, description: 'Broader research-style synthesis.' },
  { id: 'academic', label: 'Academic', icon: BookOpen, description: 'Search with academic/research intent.' },
  { id: 'news', label: 'News', icon: Newspaper, description: 'Search for recent coverage and updates.' },
  { id: 'fact-check', label: 'Fact Check', icon: ShieldCheck, description: 'Check claims against available evidence.' },
  { id: 'report', label: 'Report', icon: Sparkles, description: 'Produce a structured research report.' },
]

const examples = [
  'AI trends in healthcare for small businesses',
  'Compare Ollama, LiteLLM, and Open WebUI for a local AI hub',
  'Best open-source tools for document intelligence',
]

export default function Research() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<ResearchMode>('web')
  const [model, setModel] = useState('')
  const [models, setModels] = useState<{ name: string }[]>([])
  const [maxSources, setMaxSources] = useState(5)
  const [isLoading, setIsLoading] = useState(false)
  const [summary, setSummary] = useState('')
  const [sources, setSources] = useState<ResearchSource[]>([])
  const [history, setHistory] = useState<ResearchRun[]>([])
  const [error, setError] = useState('')
  const [activeResult, setActiveResult] = useState<ResearchRun | null>(null)
  const controller = useRef<AbortController | null>(null)
  const lastRequest = useRef<{ query: string; mode: ResearchMode; model: string; max_sources: number } | null>(null)
  const { user } = useAuth()
  const historyKey = `multimax_research_history:${user?.id || 'anonymous'}`
  const { addToast } = useToast()

  useEffect(() => {
    setSummary('')
    setSources([])
    setActiveResult(null)
    setError('')
    setIsLoading(false)
    lastRequest.current = null
    try {
      const saved = JSON.parse(localStorage.getItem(historyKey) || '[]')
      setHistory(Array.isArray(saved) ? saved.filter(item => item && typeof item.query === 'string' && typeof item.summary === 'string' && modes.some(mode => mode.id === item.mode) && Array.isArray(item.sources) && item.sources.every((source: ResearchSource) => source && typeof source.url === 'string' && typeof source.title === 'string' && typeof source.snippet === 'string')).slice(0, 20) : [])
    } catch { setHistory([]) }
    return () => { controller.current?.abort(); controller.current = null }
  }, [historyKey])

  useEffect(() => {
    let mounted = true
    getOllamaModels().then(data => {
      if (mounted && data.models?.length) {
        setModels(data.models)
        const preferred = data.models.find(item => item.name.startsWith('gemini-') && item.name.includes('flash-lite')) || data.models.find(item => item.name.startsWith('gemini-'))
        setModel(preferred?.name || '')
      }
    }).catch(() => undefined)
    return () => { mounted = false }
  }, [])

  const runResearch = async (retry = false) => {
    if (controller.current) return
    const payload = retry && lastRequest.current ? lastRequest.current : { query: query.trim(), mode, model, max_sources: maxSources }
    if (!payload.query) {
      addToast('Enter a research question first', 'error')
      return
    }
    const request = new AbortController()
    controller.current = request
    lastRequest.current = payload
    let timedOut = false
    const timeout = window.setTimeout(() => { timedOut = true; request.abort() }, 120000)
    setIsLoading(true)
    setError('')
    setActiveResult(null)
    setSummary('')
    setSources([])
    try {
      const result = await runResearchSearch(payload, request.signal)
      if (request.signal.aborted) return
      setSummary(result.summary)
      setSources(result.sources || [])
      const run = { id: crypto.randomUUID(), query: payload.query, mode: payload.mode, model: result.model, summary: result.summary, sources: result.sources || [], createdAt: new Date().toISOString() }
      setActiveResult(run)
      const next = [run, ...history].slice(0, 20)
      setHistory(next)
      try { localStorage.setItem(historyKey, JSON.stringify(next)) } catch { addToast('Answer ready, but browser history storage is full or unavailable.', 'error') }
    } catch (error: any) {
      if (controller.current !== request) return
      if (!request.signal.aborted || timedOut) setError(timedOut ? 'Research timed out. Try again or select another model.' : error.message || 'Research failed')
    } finally {
      window.clearTimeout(timeout)
      if (controller.current === request) { controller.current = null; setIsLoading(false) }
    }
  }

  const copy = async (text: string) => {
    try { await navigator.clipboard.writeText(text); addToast('Copied', 'success') }
    catch { addToast('Clipboard unavailable. Select the answer and copy it manually.', 'error') }
  }

  const exportReport = () => {
    if (!activeResult) return
    const sourceText = sources.map((source, index) => `[${index + 1}] ${source.title}\n${source.url}\n${source.snippet}`).join('\n\n')
    const blob = new Blob([`# Research: ${activeResult.query}\n\nMode: ${activeResult.mode}\nModel: ${activeResult.model || 'Not recorded'}\n\n## Answer\n${summary}\n\n## Sources\n${sourceText}`], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `multimax-research-${activeResult.mode}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Research Engine</h1>
          <p className="text-slate-500 dark:text-slate-400">Source-based answers, comparisons, news, and research reports.</p>
        </div>
        <div className="flex gap-3">
          <select aria-label="Research model" disabled={isLoading} value={model} onChange={(e) => setModel(e.target.value)} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200">
            <option value="">Automatic (configured provider)</option>
            {models.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}
          </select>
          <select aria-label="Maximum sources" disabled={isLoading} value={maxSources} onChange={(e) => setMaxSources(Number(e.target.value))} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200">
            {[3, 5, 8, 10].map(count => <option key={count} value={count}>{count} sources</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {modes.map(item => {
          const Icon = item.icon
          return (
            <button key={item.id} disabled={isLoading} aria-pressed={mode === item.id} onClick={() => setMode(item.id)} className={cn('text-left rounded-2xl border p-4 transition-all', mode === item.id ? 'border-green-500 bg-green-500/10' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-green-500/50')}>
              <div className="flex items-center gap-3 mb-2"><Icon className="w-5 h-5 text-green-500" /><span className="font-semibold text-slate-800 dark:text-slate-100">{item.label}</span></div>
              <p className="text-sm text-slate-500 dark:text-slate-400">{item.description}</p>
            </button>
          )
        })}
      </div>

      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
        <div className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input aria-label="Research question" maxLength={2000} disabled={isLoading} value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && void runResearch()} placeholder="Research anything..." className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 border-0 pl-12 pr-4 py-3 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          </div>
          <button onClick={() => void runResearch()} disabled={isLoading} className="inline-flex items-center justify-center gap-2 rounded-xl bg-green-500 px-5 py-3 font-semibold text-white hover:bg-green-600 disabled:opacity-60">
            <Search className="w-4 h-4" /> {isLoading ? 'Researching...' : 'Research'}
          </button>
          {isLoading && <button onClick={() => { controller.current?.abort(); controller.current = null; setIsLoading(false); setError('Research stopped. You can retry when ready.') }} className="rounded-xl px-4 py-2 text-slate-600 dark:text-slate-300">Stop research</button>}
        </div>
        <p className="mt-3 text-xs text-slate-500">Your question is sent to DuckDuckGo. The question and search snippets are sent to the selected AI provider. Avoid confidential information.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {examples.map(example => <button key={example} disabled={isLoading} onClick={() => setQuery(example)} className="rounded-full bg-slate-100 dark:bg-slate-800 px-3 py-1 text-xs text-slate-600 dark:text-slate-300 hover:ring-1 hover:ring-green-500">{example}</button>)}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 min-h-[460px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-800 dark:text-slate-100">Answer</h2>
            <div className="flex gap-2">
              <button aria-label="Copy answer" onClick={() => copy(summary)} disabled={!summary} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-40"><Copy className="w-4 h-4" /></button>
              <button aria-label="Export Markdown report" onClick={exportReport} disabled={!activeResult} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-40">MD</button>
            </div>
          </div>
          {error && <div role="alert" className="mb-4 rounded-xl bg-red-500/10 p-3 text-red-600 dark:text-red-400">{error}<button onClick={() => void runResearch(true)} disabled={isLoading} className="ml-3 underline">Retry</button></div>}
          <div aria-live="polite" aria-busy={isLoading} className="prose prose-slate dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary || (isLoading ? 'Searching sources and writing answer...' : 'Your cited research answer will appear here.')}</ReactMarkdown>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Sources</h2>
          <div className="space-y-3">
            {sources.length === 0 ? <p className="text-sm text-slate-500">Sources will appear after research.</p> : sources.map((source, index) => (
              <a key={`${source.url}-${index}`} href={/^https?:\/\//i.test(source.url) ? source.url : undefined} target="_blank" rel="noopener noreferrer" className="block rounded-xl bg-slate-100 dark:bg-slate-800 p-3 hover:ring-2 hover:ring-green-500">
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">[{index + 1}] {source.title}</p>
                <p className="text-xs text-green-600 dark:text-green-400 truncate">{source.url}</p>
                <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{source.snippet}</p>
              </a>
            ))}
          </div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Recent research</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {history.map(item => <button key={item.id} disabled={isLoading} onClick={() => { setQuery(item.query); setMode(item.mode); setModel(item.model || ''); setSummary(item.summary); setSources(item.sources); setActiveResult(item); setError('') }} className="text-left rounded-xl bg-slate-100 dark:bg-slate-800 p-3 hover:ring-2 hover:ring-green-500"><p className="font-medium text-slate-800 dark:text-slate-100 truncate">{item.query}</p><p className="text-xs text-slate-500">{item.mode} · {item.sources.length} sources</p></button>)}
          </div>
        </div>
      )}
    </div>
  )
}

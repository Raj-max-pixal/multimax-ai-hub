import { useEffect, useState } from 'react'
import { Bot, Copy, Play, Route, ShoppingBag, Plane, Database, FileText, Globe2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getAgentRuns, getOllamaModels, runAgent } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { cn } from '../lib/utils'

type AgentType = 'research' | 'browser' | 'shopping' | 'travel' | 'data' | 'report' | 'general'

const agentTypes: { id: AgentType; label: string; icon: any; description: string }[] = [
  { id: 'general', label: 'General Agent', icon: Bot, description: 'Plan and execute broad multi-step tasks.' },
  { id: 'research', label: 'Research Agent', icon: Globe2, description: 'Collect, compare, and summarize information.' },
  { id: 'browser', label: 'Browser Agent', icon: Route, description: 'Plan browser-controlled workflows that need approval.' },
  { id: 'shopping', label: 'Shopping Agent', icon: ShoppingBag, description: 'Compare products, prices, constraints, and reviews.' },
  { id: 'travel', label: 'Travel Agent', icon: Plane, description: 'Plan trips, itineraries, bookings, and options.' },
  { id: 'data', label: 'Data Agent', icon: Database, description: 'Collect, clean, compare, and summarize data.' },
  { id: 'report', label: 'Report Agent', icon: FileText, description: 'Turn multi-step work into a final report.' },
]

export default function Agents() {
  const [goal, setGoal] = useState('Find the best open-source stack for an AI hub and produce an action plan.')
  const [agentType, setAgentType] = useState<AgentType>('general')
  const [model, setModel] = useState('qwen3:4b')
  const [models, setModels] = useState<{ name: string }[]>([{ name: 'qwen3:4b' }, { name: 'phi3:latest' }])
  const [maxSteps, setMaxSteps] = useState(5)
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState('')
  const [runs, setRuns] = useState<any[]>([])
  const { addToast } = useToast()

  const loadRuns = () => getAgentRuns().then(data => setRuns(data.runs || [])).catch(() => undefined)

  useEffect(() => {
    getOllamaModels().then(data => data.models?.length && setModels(data.models)).catch(() => undefined)
    loadRuns()
  }, [])

  const startAgent = async () => {
    if (!goal.trim()) return addToast('Enter an agent goal first', 'error')
    setIsLoading(true)
    try {
      const data = await runAgent({ goal: goal.trim(), agent_type: agentType, model, max_steps: maxSteps })
      setResult(data.steps || '')
      await loadRuns()
    } catch (error: any) {
      addToast(error.message || 'Agent failed', 'error')
      setResult(`Error: ${error.message || 'Agent failed'}`)
    } finally {
      setIsLoading(false)
    }
  }

  const copy = async () => {
    await navigator.clipboard.writeText(result)
    addToast('Copied', 'success')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">AI Agents</h1>
        <p className="text-slate-500 dark:text-slate-400">Phase 4: multi-step agent planning for research, browser, shopping, travel, data, and reports.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {agentTypes.map(item => {
          const Icon = item.icon
          return <button key={item.id} onClick={() => setAgentType(item.id)} className={cn('text-left rounded-2xl border p-4', agentType === item.id ? 'border-green-500 bg-green-500/10' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900')}><div className="flex gap-2 items-center font-semibold text-slate-800 dark:text-slate-100"><Icon className="w-5 h-5 text-green-500" />{item.label}</div><p className="mt-2 text-sm text-slate-500">{item.description}</p></button>
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <textarea value={goal} onChange={(e) => setGoal(e.target.value)} rows={8} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <div className="flex flex-wrap gap-3">
            <select value={model} onChange={(e) => setModel(e.target.value)} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{models.map(m => <option key={m.name}>{m.name}</option>)}</select>
            <select value={maxSteps} onChange={(e) => setMaxSteps(Number(e.target.value))} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{[3,5,8,12].map(n => <option key={n} value={n}>{n} steps</option>)}</select>
            <button onClick={startAgent} disabled={isLoading} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-5 py-2 font-semibold text-white hover:bg-green-600 disabled:opacity-60"><Play className="w-4 h-4" />{isLoading ? 'Planning...' : 'Run Agent'}</button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 min-h-[380px]">
          <div className="flex items-center justify-between mb-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100">Agent Plan</h2><button onClick={copy} disabled={!result} className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg disabled:opacity-40"><Copy className="w-4 h-4" /></button></div>
          <div className="prose prose-slate dark:prose-invert max-w-none"><ReactMarkdown remarkPlugins={[remarkGfm]}>{result || (isLoading ? 'Planning agent steps...' : 'Agent output will appear here.')}</ReactMarkdown></div>
        </div>
      </div>

      {runs.length > 0 && <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Agent Runs</h2><div className="grid grid-cols-1 md:grid-cols-3 gap-3">{runs.map(run => <button key={run.id} onClick={() => setResult(run.steps)} className="text-left rounded-xl bg-slate-100 dark:bg-slate-800 p-3 hover:ring-2 hover:ring-green-500"><p className="font-medium text-slate-800 dark:text-slate-100 truncate">{run.goal}</p><p className="text-xs text-slate-500">{run.agent_type} · {run.status}</p></button>)}</div></div>}
    </div>
  )
}

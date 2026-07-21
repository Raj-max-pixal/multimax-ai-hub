import { useEffect, useState } from 'react'
import { Copy, Play, Plus, Workflow, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { createWorkflow, generateWorkflow, getOllamaModels, getWorkflows } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function Automation() {
  const [name, setName] = useState('Daily research digest')
  const [trigger, setTrigger] = useState('Every morning at 9 AM')
  const [actions, setActions] = useState('Search latest AI news\nSummarize top 5 items\nCreate a markdown report')
  const [idea, setIdea] = useState('Create a workflow that researches AI news every morning and generates a report.')
  const [model, setModel] = useState('qwen3:4b')
  const [models, setModels] = useState<{ name: string }[]>([{ name: 'qwen3:4b' }, { name: 'phi3:latest' }])
  const [workflows, setWorkflows] = useState<any[]>([])
  const [generated, setGenerated] = useState('')
  const [loading, setLoading] = useState(false)
  const { addToast } = useToast()

  const load = () => getWorkflows().then(data => setWorkflows(data.workflows || [])).catch(() => undefined)
  useEffect(() => { getOllamaModels().then(data => data.models?.length && setModels(data.models)).catch(() => undefined); load() }, [])

  const save = async () => {
    await createWorkflow({ name, trigger, actions: actions.split('\n').map(a => a.trim()).filter(Boolean), enabled: true })
    addToast('Workflow saved', 'success')
    load()
  }

  const generate = async () => {
    if (!idea.trim()) return addToast('Describe an automation idea first', 'error')
    setLoading(true)
    try {
      const data = await generateWorkflow({ query: idea, mode: 'report', model, max_sources: 3 })
      setGenerated(data.summary || '')
    } catch (e: any) {
      addToast(e.message || 'Generation failed', 'error')
      setGenerated(`Error: ${e.message || 'Generation failed'}`)
    } finally {
      setLoading(false)
    }
  }

  const copy = async () => { await navigator.clipboard.writeText(generated); addToast('Copied', 'success') }

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Workflow Automation</h1><p className="text-slate-500 dark:text-slate-400">Visual workflow planning, AI workflow generation, triggers, and action chains.</p></div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Workflow className="w-5 h-5 text-green-500" /> Workflow Builder</div>
          <input value={name} onChange={(e) => setName(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100" />
          <input value={trigger} onChange={(e) => setTrigger(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100" />
          <textarea value={actions} onChange={(e) => setActions(e.target.value)} rows={8} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100" />
          <button onClick={save} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-5 py-2 font-semibold text-white hover:bg-green-600"><Plus className="w-4 h-4" />Save Workflow</button>
        </div>
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Zap className="w-5 h-5 text-green-500" /> AI Workflow Generator</div>
          <textarea value={idea} onChange={(e) => setIdea(e.target.value)} rows={6} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100" />
          <div className="flex gap-3"><select value={model} onChange={(e) => setModel(e.target.value)} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{models.map(m => <option key={m.name}>{m.name}</option>)}</select><button onClick={generate} disabled={loading} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-5 py-2 font-semibold text-white hover:bg-green-600 disabled:opacity-60"><Play className="w-4 h-4" />{loading ? 'Generating...' : 'Generate'}</button><button onClick={copy} disabled={!generated} className="rounded-xl px-3 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40"><Copy className="w-4 h-4" /></button></div>
          <div className="prose prose-slate dark:prose-invert max-w-none rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><ReactMarkdown remarkPlugins={[remarkGfm]}>{generated || 'Generated workflow design will appear here.'}</ReactMarkdown></div>
        </div>
      </div>
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Saved Workflows</h2><div className="grid grid-cols-1 md:grid-cols-3 gap-3">{workflows.map(w => <div key={w.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100">{w.name}</p><p className="text-xs text-green-500 mt-1">Trigger: {w.trigger}</p><ol className="mt-3 list-decimal pl-4 text-sm text-slate-600 dark:text-slate-300">{w.actions?.map((a: string) => <li key={a}>{a}</li>)}</ol></div>)}</div></div>
    </div>
  )
}

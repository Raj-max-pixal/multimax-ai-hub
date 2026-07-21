import { useEffect, useState } from 'react'
import { Bot, Bug, Code2, Copy, FileCode2, GitBranch, Play, RefreshCcw, Sparkles, TestTube2, Wand2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { getOllamaModels, runCodingAssist, type CodingTask } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { cn } from '../lib/utils'

type CodingRun = {
  id: string
  task: CodingTask
  prompt: string
  language: string
  answer: string
  createdAt: string
}

const tasks: { id: CodingTask; label: string; icon: any; hint: string }[] = [
  { id: 'generate', label: 'Generate Code', icon: Code2, hint: 'Create components, scripts, utilities, and full features.' },
  { id: 'fix', label: 'Fix Bugs', icon: Bug, hint: 'Paste an error or broken code and get a corrected version.' },
  { id: 'explain', label: 'Explain Code', icon: Bot, hint: 'Understand flow, functions, architecture, and edge cases.' },
  { id: 'refactor', label: 'Refactor', icon: RefreshCcw, hint: 'Improve structure, readability, performance, and safety.' },
  { id: 'tests', label: 'Generate Tests', icon: TestTube2, hint: 'Create unit/integration tests and edge cases.' },
  { id: 'readme', label: 'README', icon: FileCode2, hint: 'Generate setup, usage, scripts, and architecture docs.' },
  { id: 'api', label: 'API Generator', icon: GitBranch, hint: 'Design endpoints, schemas, errors, and examples.' },
  { id: 'project', label: 'Project Generator', icon: Wand2, hint: 'Plan a project structure and starter implementation.' },
  { id: 'review', label: 'Code Review', icon: Sparkles, hint: 'Review for correctness, security, performance, and maintainability.' },
]

const starterPrompts: Record<CodingTask, string> = {
  generate: 'Build a reusable React component for...',
  fix: 'Fix this error and explain why it happened:',
  explain: 'Explain this code clearly for a beginner:',
  refactor: 'Refactor this code without changing behavior:',
  tests: 'Generate tests for this function/component:',
  readme: 'Create a README for this project:',
  api: 'Generate a FastAPI endpoint for...',
  project: 'Create a starter project for...',
  review: 'Review this code and list improvements:',
}

export default function AICoding() {
  const [task, setTask] = useState<CodingTask>('generate')
  const [prompt, setPrompt] = useState(starterPrompts.generate)
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('TypeScript')
  const [model, setModel] = useState('qwen3:4b')
  const [models, setModels] = useState<{ name: string }[]>([{ name: 'qwen3:4b' }, { name: 'phi3:latest' }, { name: 'llama3:latest' }])
  const [isLoading, setIsLoading] = useState(false)
  const [answer, setAnswer] = useState('')
  const [history, setHistory] = useState<CodingRun[]>(() => {
    try { return JSON.parse(localStorage.getItem('multimax_coding_history') || '[]') } catch { return [] }
  })
  const { addToast } = useToast()

  useEffect(() => {
    localStorage.setItem('multimax_coding_history', JSON.stringify(history))
  }, [history])

  useEffect(() => {
    getOllamaModels().then(data => {
      if (data.models?.length) setModels(data.models)
    }).catch(() => undefined)
  }, [])

  const selectTask = (nextTask: CodingTask) => {
    setTask(nextTask)
    setPrompt(starterPrompts[nextTask])
  }

  const runAssistant = async () => {
    if (!prompt.trim() && !code.trim()) {
      addToast('Add a request or paste code first', 'error')
      return
    }
    setIsLoading(true)
    setAnswer('')
    try {
      const result = await runCodingAssist({ task, prompt, code, language, model })
      const output = result.answer || 'No response returned.'
      setAnswer(output)
      setHistory(prev => [{ id: Date.now().toString(), task, prompt, language, answer: output, createdAt: new Date().toISOString() }, ...prev].slice(0, 20))
    } catch (error: any) {
      addToast(error.message || 'Coding assistant failed', 'error')
      setAnswer(`Error: ${error.message || 'Coding assistant failed'}`)
    } finally {
      setIsLoading(false)
    }
  }

  const copy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    addToast('Copied', 'success')
  }

  const exportMarkdown = () => {
    if (!answer) return
    const blob = new Blob([`# Multimax Coding Assistant\n\nTask: ${task}\nLanguage: ${language}\nModel: ${model}\n\n## Request\n${prompt}\n\n## Code\n\
\
\
${code}\n\
\
\
\n## Answer\n${answer}`], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `multimax-coding-${task}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">AI Coding Assistant</h1>
          <p className="text-slate-500 dark:text-slate-400">Phase 2: generate, fix, explain, refactor, test, document, and review code.</p>
        </div>
        <div className="flex gap-3">
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200">
            {['TypeScript', 'Python', 'JavaScript', 'React', 'FastAPI', 'Node.js', 'SQL', 'Flutter', 'Java', 'Auto-detect'].map(item => <option key={item}>{item}</option>)}
          </select>
          <select value={model} onChange={(e) => setModel(e.target.value)} className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2 text-slate-700 dark:text-slate-200">
            {models.map(item => <option key={item.name} value={item.name}>{item.name}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {tasks.map(item => {
          const Icon = item.icon
          return (
            <button key={item.id} onClick={() => selectTask(item.id)} className={cn('text-left rounded-2xl border p-4 transition-all', task === item.id ? 'border-green-500 bg-green-500/10' : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-green-500/50')}>
              <div className="flex items-center gap-3 mb-2"><Icon className="w-5 h-5 text-green-500" /><span className="font-semibold text-slate-800 dark:text-slate-100">{item.label}</span></div>
              <p className="text-sm text-slate-500 dark:text-slate-400">{item.hint}</p>
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Request</label>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={5} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 border-0 p-4 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Code / error / project context</label>
          <textarea value={code} onChange={(e) => setCode(e.target.value)} rows={14} placeholder="Paste code, stack trace, API requirements, or repository notes..." className="font-mono text-sm w-full rounded-xl bg-slate-950 text-slate-100 border-0 p-4 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <button onClick={runAssistant} disabled={isLoading} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-5 py-3 font-semibold text-white hover:bg-green-600 disabled:opacity-60">
            <Play className="w-4 h-4" /> {isLoading ? 'Thinking...' : 'Run Coding Assistant'}
          </button>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 min-h-[520px]">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-800 dark:text-slate-100">Result</h2>
            <div className="flex gap-2">
              <button onClick={() => copy(answer)} disabled={!answer} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-40"><Copy className="w-4 h-4" /></button>
              <button onClick={exportMarkdown} disabled={!answer} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 disabled:opacity-40">MD</button>
            </div>
          </div>
          <div className="prose prose-slate dark:prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code({ inline, className, children, ...props }: any) { const match = /language-(\w+)/.exec(className || ''); return !inline && match ? <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" className="rounded-xl" {...props}>{String(children).replace(/\n$/, '')}</SyntaxHighlighter> : <code className={className} {...props}>{children}</code> } }}>
              {answer || (isLoading ? 'Generating coding response...' : 'Your coding assistant output will appear here.')}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {history.length > 0 && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Recent coding runs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {history.map(item => <button key={item.id} onClick={() => { setTask(item.task); setPrompt(item.prompt); setLanguage(item.language); setAnswer(item.answer) }} className="text-left rounded-xl bg-slate-100 dark:bg-slate-800 p-3 hover:ring-2 hover:ring-green-500"><p className="font-medium text-slate-800 dark:text-slate-100">{item.task}</p><p className="text-xs text-slate-500 truncate">{item.prompt}</p></button>)}
          </div>
        </div>
      )}
    </div>
  )
}

import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Bot, Bug, Check, Code2, Copy, FileCode2, Folder, GitBranch, GitCommit, LoaderCircle, Play, RefreshCcw, Search, Sparkles, TestTube2, Terminal as TerminalIcon, Upload, Wand2, X, Square } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { applyProjectCodingPatch, connectProjectGit, createProjectGitCommit, getCodingProjectFiles, getCodingProjects, getCodingWorkspaces, getProjectGitDiff, getProjectGitStatus, getProjectTerminalCapabilities, readCodingProjectFile, runProjectCodingAction, runProjectTerminalCommand, runProjectTests, searchCodingProjectContent, suggestProjectCommitMessage, uploadCodingProjectFile, getOllamaModels, runCodingAssist, type CodingProject, type CodingProjectFile, type CodingProposal, type CodingTask, type CodingWorkspace, type ProjectGitStatus, type TerminalCapabilities, type TerminalRunResult } from '../lib/api'
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

type AgentTurn = { role: 'user' | 'assistant'; content: string }
type ActivityItem = { label: string; state: 'done' | 'active' | 'error' }
const CodeBlock = lazy(() => import('../components/CodeBlock'))

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
  const [workspaces, setWorkspaces] = useState<CodingWorkspace[]>([])
  const [projects, setProjects] = useState<CodingProject[]>([])
  const [workspaceId, setWorkspaceId] = useState(() => localStorage.getItem('multimax_coding_workspace') || '')
  const [projectId, setProjectId] = useState(() => localStorage.getItem('multimax_coding_project') || '')
  const [files, setFiles] = useState<CodingProjectFile[]>([])
  const [fileQuery, setFileQuery] = useState('')
  const [codeSearchResults, setCodeSearchResults] = useState<{ path: string; line: number; snippet: string }[]>([])
  const [codeSearchLoading, setCodeSearchLoading] = useState(false)
  const [activePath, setActivePath] = useState('')
  const [agentPrompt, setAgentPrompt] = useState('')
  const [selectedCode, setSelectedCode] = useState('')
  const [fileLoading, setFileLoading] = useState(false)
  const [projectError, setProjectError] = useState('')
  const [agentError, setAgentError] = useState('')
  const [proposal, setProposal] = useState<CodingProposal | null>(null)
  const [activity, setActivity] = useState<ActivityItem[]>([])
  const [projectTurns, setProjectTurns] = useState<Record<string, AgentTurn[]>>(() => {
    try { return JSON.parse(localStorage.getItem('multimax_coding_project_turns') || '{}') } catch { return {} }
  })
  const [lastAction, setLastAction] = useState<{ mode: 'explain' | 'suggest' | 'patch'; prompt: string } | null>(null)
  const [uploading, setUploading] = useState(false)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [gitStatus, setGitStatus] = useState<ProjectGitStatus | null>(null)
  const [gitRepositoryUrl, setGitRepositoryUrl] = useState('')
  const [gitDefaultBranch, setGitDefaultBranch] = useState('main')
  const [gitDiff, setGitDiff] = useState('')
  const [gitDiffTruncated, setGitDiffTruncated] = useState(false)
  const [showGitDiff, setShowGitDiff] = useState(false)
  const [gitCommitMessage, setGitCommitMessage] = useState('')
  const [gitLoading, setGitLoading] = useState(false)
  const [gitError, setGitError] = useState('')
  const [gitConfirmOpen, setGitConfirmOpen] = useState(false)
  const [gitConfirmChecked, setGitConfirmChecked] = useState(false)
  const [gitActivity, setGitActivity] = useState<string[]>([])
  const [terminalCapabilities, setTerminalCapabilities] = useState<TerminalCapabilities | null>(null)
  const [terminalCommand, setTerminalCommand] = useState('')
  const [terminalResult, setTerminalResult] = useState<TerminalRunResult | null>(null)
  const [terminalError, setTerminalError] = useState('')
  const [terminalRunning, setTerminalRunning] = useState(false)
  const [terminalMode, setTerminalMode] = useState<'command' | 'tests'>('command')
  const terminalController = useRef<AbortController | null>(null)
  const [history, setHistory] = useState<CodingRun[]>(() => {
    try { return JSON.parse(localStorage.getItem('multimax_coding_history') || '[]') } catch { return [] }
  })
  const { addToast } = useToast()

  useEffect(() => {
    localStorage.setItem('multimax_coding_history', JSON.stringify(history))
  }, [history])

  useEffect(() => {
    localStorage.setItem('multimax_coding_project', projectId)
    localStorage.setItem('multimax_coding_workspace', workspaceId)
  }, [projectId, workspaceId])

  useEffect(() => {
    localStorage.setItem('multimax_coding_project_turns', JSON.stringify(projectTurns))
  }, [projectTurns])

  useEffect(() => {
    let active = true
    getCodingWorkspaces().then(data => {
      if (!active) return
      setWorkspaces(data.items || [])
      const nextId = (data.items || []).some(item => item.id === workspaceId) ? workspaceId : data.items?.[0]?.id || ''
      if (nextId !== workspaceId) setWorkspaceId(nextId)
    }).catch(error => { if (active) setProjectError(error.message || 'Unable to load workspaces') })
    return () => { active = false }
  }, [])

  useEffect(() => {
    let active = true
    if (!workspaceId) { setProjects([]); setProjectId(''); return }
    getCodingProjects(workspaceId).then(data => {
      if (!active) return
      const nextProjects = data.items || []
      setProjects(nextProjects)
      const nextId = nextProjects.some(item => item.id === projectId) ? projectId : nextProjects[0]?.id || ''
      if (nextId !== projectId) setProjectId(nextId)
    }).catch(error => { if (active) setProjectError(error.message || 'Unable to load projects') })
    return () => { active = false }
  }, [workspaceId])

  useEffect(() => {
    let active = true
    setActivePath('')
    setCode('')
    setProposal(null)
    setCodeSearchResults([])
    if (!projectId) { setFiles([]); return }
    getCodingProjectFiles(projectId, fileQuery).then(data => {
      if (active) { setFiles(data.items || []); setProjectError('') }
    }).catch(error => { if (active) setProjectError(error.message || 'Unable to list project files') })
    return () => { active = false }
  }, [projectId, fileQuery])

  useEffect(() => {
    getOllamaModels().then(data => {
      if (data.models?.length) setModels(data.models)
    }).catch(() => undefined)
  }, [])

  useEffect(() => {
    let active = true
    setGitStatus(null)
    setGitDiff('')
    setShowGitDiff(false)
    setGitError('')
    setGitActivity([])
    setGitRepositoryUrl('')
    setGitDefaultBranch('main')
    if (!projectId) return () => { active = false }
    setGitActivity(['Checking repository…'])
    getProjectGitStatus(projectId).then(status => {
      if (!active) return
      setGitStatus(status)
      if (status.repository_url) setGitRepositoryUrl(status.repository_url)
      if (status.default_branch) setGitDefaultBranch(status.default_branch)
      setGitActivity(['✓ Checking repository', '✓ Reading Git status'])
    }).catch(error => {
      if (active) {
        setGitError(error.message || 'Unable to read Git status')
        setGitActivity(['✕ Checking repository'])
      }
    })
    return () => { active = false }
  }, [projectId])

  useEffect(() => {
    let active = true
    setTerminalCapabilities(null)
    setTerminalResult(null)
    setTerminalError('')
    if (!projectId) return () => { active = false }
    getProjectTerminalCapabilities(projectId).then(value => { if (active) setTerminalCapabilities(value) })
      .catch(error => { if (active) setTerminalError(error.message || 'Unable to check secure terminal availability') })
    return () => { active = false; terminalController.current?.abort() }
  }, [projectId])

  const selectTask = (nextTask: CodingTask) => {
    setTask(nextTask)
    setPrompt(starterPrompts[nextTask])
  }

  const activeProject = projects.find(project => project.id === projectId)
  const turns = projectId ? projectTurns[projectId] || [] : []
  const directories = Array.from(new Set(files.flatMap(file => {
    const segments = file.path.split('/')
    return segments.slice(0, -1).map((_, index) => segments.slice(0, index + 1).join('/'))
  }))).sort((left, right) => left.localeCompare(right))

  const refreshGitStatus = async () => {
    if (!projectId || gitLoading) return
    setGitLoading(true)
    setGitError('')
    setGitActivity(['Checking repository…'])
    try {
      const status = await getProjectGitStatus(projectId)
      setGitStatus(status)
      setGitActivity(['✓ Checking repository', '✓ Reading Git status'])
    } catch (error: any) {
      setGitError(error.message || 'Unable to read Git status')
      setGitActivity(['✕ Checking repository'])
    } finally {
      setGitLoading(false)
    }
  }

  const connectGitRepository = async () => {
    if (!projectId || gitLoading) return
    setGitLoading(true)
    setGitError('')
    setGitActivity(['Checking repository…'])
    try {
      const status = await connectProjectGit(projectId, gitRepositoryUrl, gitDefaultBranch)
      setGitStatus(status)
      setGitActivity(['✓ Checking repository', '✓ Reading Git status', '✓ Repository associated'])
      setShowGitDiff(false)
    } catch (error: any) {
      setGitError(error.message || 'Repository could not be associated')
      setGitActivity(['✕ Checking repository'])
    } finally {
      setGitLoading(false)
    }
  }

  const inspectGitDiff = async () => {
    if (!projectId || gitLoading) return
    setGitLoading(true)
    setGitError('')
    try {
      const result = await getProjectGitDiff(projectId)
      setGitDiff(result.diff)
      setGitDiffTruncated(result.truncated)
      setShowGitDiff(true)
      setGitActivity(current => [...current, '✓ Reviewing changes'])
    } catch (error: any) {
      setGitError(error.message || 'Unable to read Git diff')
    } finally {
      setGitLoading(false)
    }
  }

  const generateCommitMessage = async () => {
    if (!projectId || gitLoading) return
    setGitLoading(true)
    setGitError('')
    setGitActivity(current => [...current, 'Reviewing changes…'])
    try {
      const result = await suggestProjectCommitMessage(projectId, model)
      setGitCommitMessage(result.message)
      setGitActivity(current => [...current.filter(item => !item.endsWith('…')), '✓ Reviewing changes', '✓ Generated commit message'])
    } catch (error: any) {
      setGitError(error.message || 'Could not suggest a commit message')
      setGitActivity(current => [...current.filter(item => !item.endsWith('…')), '✕ Reviewing changes'])
    } finally {
      setGitLoading(false)
    }
  }

  const commitGitChanges = async () => {
    if (!projectId || !gitConfirmChecked || !gitCommitMessage.trim() || gitLoading) return
    setGitLoading(true)
    setGitError('')
    try {
      const result = await createProjectGitCommit(projectId, gitCommitMessage, true)
      setGitConfirmOpen(false)
      setGitConfirmChecked(false)
      setGitActivity(current => [...current, `✓ Created commit ${result.commit}`])
      const [status, diff] = await Promise.all([getProjectGitStatus(projectId), getProjectGitDiff(projectId)])
      setGitStatus(status)
      setGitDiff(diff.diff)
      setGitDiffTruncated(diff.truncated)
      setShowGitDiff(true)
    } catch (error: any) {
      setGitError(error.message || 'Commit failed; your changes were not pushed')
    } finally {
      setGitLoading(false)
    }
  }

  const executeTerminal = async (mode: 'command' | 'tests') => {
    if (!projectId || terminalRunning || !terminalCapabilities?.available) return
    const argv = terminalCommand.trim().split(/\s+/).filter(Boolean)
    if (mode === 'command' && !argv.length) { setTerminalError('Enter an allowlisted command.'); return }
    const controller = new AbortController()
    terminalController.current = controller
    setTerminalMode(mode)
    setTerminalRunning(true)
    setTerminalError('')
    setTerminalResult(null)
    setActivity(current => [...current, { label: mode === 'tests' ? 'Running project tests' : `Running ${argv[0]}`, state: 'active' }])
    try {
      const result = mode === 'tests'
        ? await runProjectTests(projectId, controller.signal)
        : await runProjectTerminalCommand(projectId, argv, controller.signal)
      setTerminalResult(result)
      const passed = result.exit_code === 0 && !result.timed_out
      setActivity(current => [...current.filter(item => item.state !== 'active'), {
        label: mode === 'tests' ? (passed ? 'Tests passed' : 'Tests failed') : `Command exited ${result.exit_code}`,
        state: passed ? 'done' : 'error',
      }])
    } catch (error: any) {
      if (error.name === 'AbortError') {
        setActivity(current => [...current.filter(item => item.state !== 'active'), { label: 'Command cancelled', state: 'error' }])
      } else {
        setTerminalError(error.message || 'Command could not run')
        setActivity(current => [...current.filter(item => item.state !== 'active'), { label: mode === 'tests' ? 'Tests failed to start' : 'Command failed to start', state: 'error' }])
      }
    } finally {
      terminalController.current = null
      setTerminalRunning(false)
    }
  }

  const askAgentToFixTests = () => {
    if (!terminalResult || terminalResult.exit_code === 0 || !projectId) return
    const details = `${terminalResult.stdout}\n${terminalResult.stderr}`.trim().slice(-5000)
    const requestText = `Analyze this actual test failure and propose a focused fix. Do not claim tests pass unless rerun successfully.\n\nCommand: ${terminalResult.command}\nExit code: ${terminalResult.exit_code}\nOutput:\n${details}`
    setAgentPrompt(requestText)
    void runProjectAction(activePath ? 'patch' : 'suggest', requestText)
  }

  const openProjectFile = async (path: string) => {
    if (!projectId) return
    setFileLoading(true)
    setProjectError('')
    setActivity([{ label: `Reading ${path}`, state: 'active' }])
    try {
      const result = await readCodingProjectFile(projectId, path)
      setActivePath(result.path)
      setCode(result.content)
      setSelectedCode('')
      setActivity([{ label: `Read ${path}`, state: 'done' }])
    } catch (error: any) {
      setProjectError(error.message || `Could not open ${path}`)
      setActivity([{ label: `Could not read ${path}`, state: 'error' }])
    } finally {
      setFileLoading(false)
    }
  }

  const searchProjectContent = async () => {
    if (!projectId || fileQuery.trim().length < 2 || codeSearchLoading) return
    setCodeSearchLoading(true)
    setProjectError('')
    try {
      const result = await searchCodingProjectContent(projectId, fileQuery.trim())
      setCodeSearchResults(result.items || [])
      if (!result.items?.length) setProjectError('No matching source lines found.')
    } catch (error: any) {
      setProjectError(error.message || 'Repository code search failed')
    } finally {
      setCodeSearchLoading(false)
    }
  }

  const addProjectFiles = async (selected: FileList | null) => {
    if (!projectId || !selected?.length) return
    setUploading(true)
    setProjectError('')
    try {
      for (const file of Array.from(selected)) {
        const relativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name
        await uploadCodingProjectFile(projectId, file, relativePath)
      }
      const result = await getCodingProjectFiles(projectId, fileQuery)
      setFiles(result.items || [])
    } catch (error: any) {
      setProjectError(error.message || 'Some project files could not be added')
    } finally {
      setUploading(false)
      setFileInputKey(key => key + 1)
    }
  }

  const runProjectAction = async (mode: 'explain' | 'suggest' | 'patch', requestText = agentPrompt) => {
    if (!projectId || isLoading) return
    if (!requestText.trim()) { setAgentError('Describe what you want the agent to do.'); return }
    if (mode === 'patch' && !activePath) { setAgentError('Open a project file before proposing a patch.'); return }
    setLastAction({ mode, prompt: requestText })
    setAgentError('')
    setProposal(null)
    setIsLoading(true)
    setActivity([
      ...(activePath ? [{ label: `Read ${activePath}`, state: 'done' as const }] : []),
      { label: 'Searching project files', state: 'done' },
      { label: 'Analyzing code', state: 'active' },
      ...(mode === 'patch' ? [{ label: 'Preparing proposed changes', state: 'active' as const }] : []),
    ])
    const previousTurns = turns
    try {
      const result = await runProjectCodingAction({
        project_id: projectId, mode, prompt: requestText, path: activePath || undefined,
        selected_code: selectedCode || undefined, history: previousTurns, model,
      })
      if (result.mode === 'patch') {
        setProposal(result)
        setAnswer(`${result.summary}\n\nProposed diff for ${result.path}`)
        setProjectTurns(prev => ({ ...prev, [projectId]: [...(prev[projectId] || []), { role: 'user' as const, content: requestText }, { role: 'assistant' as const, content: result.summary }].slice(-16) }))
      } else {
        setAnswer(result.answer)
        setProjectTurns(prev => ({ ...prev, [projectId]: [...(prev[projectId] || []), { role: 'user' as const, content: requestText }, { role: 'assistant' as const, content: result.answer }].slice(-16) }))
      }
      setActivity(current => current.map(item => ({ ...item, state: 'done' })))
    } catch (error: any) {
      setAgentError(error.message || 'Coding request failed. Retry when ready.')
      setActivity(current => current.map(item => item.state === 'active' ? { ...item, state: 'error' } : item))
    } finally {
      setIsLoading(false)
    }
  }

  const applyProposal = async () => {
    if (!projectId || !proposal || isLoading) return
    setIsLoading(true)
    setAgentError('')
    setActivity([{ label: `Applying reviewed patch to ${proposal.path}`, state: 'active' }])
    try {
      await applyProjectCodingPatch(projectId, proposal)
      setProposal(null)
      await openProjectFile(activePath)
      setActivity([{ label: `Applied changes to ${activePath}`, state: 'done' }])
    } catch (error: any) {
      setAgentError(error.message || 'Patch could not be applied. Reopen the file and try again.')
      setActivity([{ label: 'Patch was not applied', state: 'error' }])
    } finally {
      setIsLoading(false)
    }
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

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-4 dark:border-slate-800">
          <div>
            <h2 className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Folder className="h-5 w-5 text-green-500" />Repository workspace</h2>
            <p className="mt-1 text-sm text-slate-500">Choose a project to inspect files and review AI-proposed patches.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select aria-label="Workspace" value={workspaceId} onChange={event => { setWorkspaceId(event.target.value); setProjectId('') }} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
              <option value="">Select workspace</option>{workspaces.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            <select aria-label="Project" value={projectId} onChange={event => setProjectId(event.target.value)} disabled={!projects.length} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
              <option value="">Select project</option>{projects.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
            {projectId && <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700">
              {uploading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}{uploading ? 'Adding files…' : 'Add project files'}
              <input key={fileInputKey} type="file" multiple className="hidden" disabled={uploading || isLoading} onChange={event => void addProjectFiles(event.target.files)} />
            </label>}
          </div>
        </div>
        {projectError && <div role="alert" className="m-4 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">{projectError}</div>}
        {activeProject ? <div className="grid min-h-[420px] lg:grid-cols-[260px_minmax(0,1fr)]">
          <aside className="border-b border-slate-200 p-3 dark:border-slate-800 lg:border-b-0 lg:border-r">
            <div className="mb-3 flex items-center justify-between gap-2"><div className="min-w-0"><p className="text-xs uppercase tracking-wide text-slate-500">Active project</p><p className="truncate font-semibold text-slate-800 dark:text-slate-100" title={activeProject.name}>{activeProject.name}</p></div><span className="rounded-full bg-green-500/10 px-2 py-1 text-xs text-green-600">{files.length} files</span></div>
            <label className="relative mb-3 block"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" /><input value={fileQuery} onChange={event => setFileQuery(event.target.value)} placeholder="Search project files" className="w-full rounded-lg bg-slate-100 py-2 pl-9 pr-3 text-sm text-slate-700 outline-none focus:ring-2 focus:ring-green-500 dark:bg-slate-800 dark:text-slate-200" /></label>
            <button onClick={() => void searchProjectContent()} disabled={codeSearchLoading || fileQuery.trim().length < 2} className="mb-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-left text-xs font-medium text-slate-600 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300">{codeSearchLoading ? 'Searching source…' : 'Search inside project files'}</button>
            {codeSearchResults.length > 0 && <div className="mb-3 space-y-1" aria-label="Code search results"><p className="px-2 text-xs font-medium text-slate-500">Source matches</p>{codeSearchResults.map(result => <button key={`${result.path}:${result.line}`} onClick={() => void openProjectFile(result.path)} className="w-full rounded-lg bg-slate-50 p-2 text-left hover:bg-green-50 dark:bg-slate-800/70 dark:hover:bg-green-950/30"><span className="block truncate text-xs font-medium text-green-700 dark:text-green-300">{result.path}:{result.line}</span><code className="mt-1 block truncate text-[11px] text-slate-500">{result.snippet}</code></button>)}</div>}
            <div className="max-h-72 space-y-1 overflow-auto" aria-label="Project files">
              {directories.map(directory => <div key={`dir:${directory}`} className="flex items-center gap-2 px-2 py-1 text-xs text-slate-400"><Folder className="h-3.5 w-3.5" /><span className="truncate">{directory}/</span></div>)}
              {files.map(file => <button key={file.path} onClick={() => void openProjectFile(file.path)} className={cn('flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm', activePath === file.path ? 'bg-green-500/10 text-green-700 dark:text-green-300' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800')}><FileCode2 className="h-4 w-4 shrink-0" /><span className="truncate" title={file.path}>{file.path}</span></button>)}
              {!files.length && <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500 dark:bg-slate-800/60">No project files yet. Add source files to begin.</p>}
            </div>
          </aside>
          <div className="grid min-w-0 gap-4 p-4 xl:grid-cols-2">
            <div className="min-w-0 space-y-3">
              <div className="flex items-center justify-between"><h3 className="font-medium text-slate-800 dark:text-slate-100">{activePath || 'Open a file to inspect'}</h3>{fileLoading && <LoaderCircle className="h-4 w-4 animate-spin text-green-500" />}</div>
              <textarea value={code} onSelect={event => { const target = event.currentTarget; const selection = target.value.slice(target.selectionStart, target.selectionEnd).trim(); if (selection) setSelectedCode(selection) }} readOnly rows={14} placeholder="Select a project file from the explorer. File content is displayed with detected credentials redacted." className="w-full resize-y rounded-xl bg-slate-950 p-4 font-mono text-xs leading-6 text-slate-100 outline-none focus:ring-2 focus:ring-green-500" />
              {selectedCode && <p className="text-xs text-green-600">Selected code will be included as focused context.</p>}
              <textarea value={agentPrompt} onChange={event => setAgentPrompt(event.target.value)} rows={2} placeholder="Ask about this project or describe a change…" className="w-full rounded-xl bg-slate-100 p-3 text-sm text-slate-800 outline-none focus:ring-2 focus:ring-green-500 dark:bg-slate-800 dark:text-slate-100" />
              <div className="flex flex-wrap gap-2">
                <button onClick={() => void runProjectAction('explain')} disabled={isLoading || !activePath} className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-200">Explain file</button>
                <button onClick={() => void runProjectAction('suggest')} disabled={isLoading || !activePath} className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-200">Suggest improvements</button>
                <button onClick={() => void runProjectAction('patch')} disabled={isLoading || !activePath} className="rounded-lg bg-green-500 px-3 py-2 text-sm font-medium text-white hover:bg-green-600 disabled:opacity-50">Propose patch</button>
              </div>
            </div>
            <div className="min-w-0 space-y-4">
              <div className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                <h3 className="mb-3 flex items-center gap-2 font-medium text-slate-800 dark:text-slate-100"><Bot className="h-4 w-4 text-green-500" />Agent activity</h3>
                {activity.length ? <ol className="space-y-2">{activity.map((item, index) => <li key={`${item.label}-${index}`} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">{item.state === 'done' ? <Check className="h-4 w-4 text-green-500" /> : item.state === 'error' ? <X className="h-4 w-4 text-red-500" /> : <LoaderCircle className="h-4 w-4 animate-spin text-green-500" />}{item.label}</li>)}</ol> : <p className="text-sm text-slate-500">File reads and coding actions will appear here.</p>}
              </div>
              {agentError && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200"><p>{agentError}</p>{lastAction && <button onClick={() => void runProjectAction(lastAction.mode, lastAction.prompt)} disabled={isLoading} className="mt-2 font-medium underline disabled:opacity-50">Retry request</button>}</div>}
              {proposal && <div className="overflow-hidden rounded-xl border border-amber-300 dark:border-amber-900"><div className="flex flex-wrap items-center justify-between gap-2 bg-amber-50 px-3 py-2 dark:bg-amber-950/30"><div><p className="font-medium text-slate-800 dark:text-slate-100">Review proposed change</p><p className="text-xs text-slate-500">{proposal.summary} · {proposal.path}</p></div><div className="flex gap-2"><button onClick={() => void applyProposal()} disabled={isLoading} className="rounded-lg bg-green-600 px-3 py-1.5 text-sm text-white disabled:opacity-50">Apply</button><button onClick={() => setProposal(null)} disabled={isLoading} className="rounded-lg bg-slate-200 px-3 py-1.5 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">Reject</button></div></div><pre className="max-h-80 overflow-auto bg-slate-950 p-3 text-xs leading-5">{proposal.diff.split('\n').map((line, index) => <span key={index} className={cn('block', line.startsWith('+') && !line.startsWith('+++') && 'bg-green-950/70 text-green-300', line.startsWith('-') && !line.startsWith('---') && 'bg-red-950/70 text-red-300', line.startsWith('@@') && 'text-sky-300')}>{line || ' '}</span>)}</pre></div>}
              {turns.length > 0 && <div className="max-h-56 space-y-2 overflow-auto rounded-xl border border-slate-200 p-3 dark:border-slate-800"><h3 className="text-xs font-medium uppercase tracking-wide text-slate-500">Project coding conversation</h3>{turns.map((turn, index) => <div key={index} className={cn('rounded-lg px-3 py-2 text-sm whitespace-pre-wrap', turn.role === 'user' ? 'ml-6 bg-blue-500/10 text-slate-700 dark:text-slate-200' : 'mr-6 bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200')}>{turn.content}</div>)}</div>}
            </div>
          </div>
        </div> : <div className="p-8 text-center text-sm text-slate-500">{workspaces.length ? 'Choose a workspace with a project to start.' : 'No accessible workspaces found. Create or join one to use repository context.'}</div>}
      </section>

      {activeProject && <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><h2 className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><GitBranch className="h-5 w-5 text-green-500" />Git integration</h2><p className="mt-1 text-sm text-slate-500">Project-scoped local status and commits. GitHub/GitLab OAuth and push are not enabled.</p></div>
          {gitStatus?.is_git_repository && <span className={cn('rounded-full px-3 py-1 text-xs font-medium', gitStatus.state === 'clean' ? 'bg-green-500/10 text-green-600' : 'bg-amber-500/10 text-amber-600')}>{gitStatus.state === 'clean' ? 'Clean' : 'Dirty'} · {gitStatus.branch}</span>}
        </div>

        {gitError && <div role="alert" className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">{gitError}</div>}
        {gitStatus?.is_git_repository ? <>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-300"><span><strong>Provider:</strong> {gitStatus.provider || 'Generic'}</span><span><strong>Branch:</strong> {gitStatus.branch || 'Unknown'}</span><span><strong>Default:</strong> {gitStatus.default_branch || 'Not set'}</span><span className="max-w-full truncate" title={gitStatus.repository_url || ''}><strong>Remote:</strong> {gitStatus.repository_url || 'Not configured'}</span></div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {([
              ['Modified', gitStatus.modified_files], ['Untracked', gitStatus.untracked_files],
              ['Staged', gitStatus.staged_files], ['Deleted', gitStatus.deleted_files],
            ] as const).map(([label, paths]) => <div key={label} className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800/70"><h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">{label} · {paths.length}</h3>{paths.length ? <ul className="max-h-28 space-y-1 overflow-auto text-xs text-slate-700 dark:text-slate-200">{paths.map(path => <li key={path} className="truncate" title={path}>{path}</li>)}</ul> : <p className="text-xs text-slate-400">None</p>}</div>)}
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => void refreshGitStatus()} disabled={gitLoading} className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-200">{gitLoading ? 'Working…' : 'Refresh status'}</button>
            <button onClick={() => void inspectGitDiff()} disabled={gitLoading} className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-200">Review Git diff</button>
            <button onClick={() => void generateCommitMessage()} disabled={gitLoading || gitStatus.state === 'clean'} className="rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-200">{gitLoading ? 'Working…' : 'Suggest commit message'}</button>
          </div>
          {gitCommitMessage !== '' && <div className="space-y-2 rounded-xl border border-slate-200 p-3 dark:border-slate-700">
            <label htmlFor="git-commit-message" className="text-sm font-medium text-slate-700 dark:text-slate-200">Commit message (editable)</label>
            <input id="git-commit-message" value={gitCommitMessage} onChange={event => setGitCommitMessage(event.target.value)} maxLength={200} className="w-full rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-100" />
            {!gitConfirmOpen ? <button onClick={() => { setGitConfirmChecked(false); setGitConfirmOpen(true) }} disabled={gitLoading || !gitCommitMessage.trim() || gitStatus.state === 'clean'} className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"><GitCommit className="h-4 w-4" />Review and commit locally</button> : <div className="space-y-3 rounded-lg bg-amber-50 p-3 dark:bg-amber-950/20">
              <p className="text-sm text-slate-700 dark:text-slate-200">This stages the project’s non-sensitive changes and creates a local commit. Nothing will be pushed.</p>
              <label className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-200"><input type="checkbox" checked={gitConfirmChecked} onChange={event => setGitConfirmChecked(event.target.checked)} className="mt-1" />I reviewed the changes and explicitly confirm this local commit.</label>
              <div className="flex gap-2"><button onClick={() => void commitGitChanges()} disabled={!gitConfirmChecked || gitLoading} className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-50">{gitLoading ? 'Committing…' : 'Confirm and commit'}</button><button onClick={() => setGitConfirmOpen(false)} disabled={gitLoading} className="rounded-lg bg-slate-200 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200">Cancel</button></div>
            </div>}
          </div>}
        </> : <div className="grid gap-3 rounded-xl bg-slate-50 p-4 dark:bg-slate-800/60 md:grid-cols-[minmax(0,1fr)_180px_auto] md:items-end">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Public HTTPS repository URL<input type="url" value={gitRepositoryUrl} onChange={event => setGitRepositoryUrl(event.target.value)} placeholder="https://github.com/owner/repository.git" className="mt-1 w-full rounded-lg bg-white px-3 py-2 text-sm font-normal dark:bg-slate-900" /></label>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200">Default branch<input value={gitDefaultBranch} onChange={event => setGitDefaultBranch(event.target.value)} maxLength={200} placeholder="main" className="mt-1 w-full rounded-lg bg-white px-3 py-2 text-sm font-normal dark:bg-slate-900" /></label>
          <button onClick={() => void connectGitRepository()} disabled={gitLoading || !gitRepositoryUrl.trim() || !gitDefaultBranch.trim()} className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{gitLoading ? 'Checking…' : 'Associate repository'}</button>
          <p className="text-xs text-slate-500 md:col-span-3">Associates the URL with this project and initializes Git over its managed files if needed. No clone, fetch, credential storage, or push is performed.</p>
        </div>}
        {gitActivity.length > 0 && <ol aria-live="polite" className="space-y-1 text-sm text-slate-500">{gitActivity.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ol>}
        {showGitDiff && <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800"><div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 text-sm dark:border-slate-800"><span className="font-medium text-slate-700 dark:text-slate-200">Project diff</span><button onClick={() => setShowGitDiff(false)} aria-label="Close Git diff" className="text-slate-500 hover:text-slate-800 dark:hover:text-white"><X className="h-4 w-4" /></button></div>{gitDiff ? <pre className="max-h-[480px] overflow-auto bg-slate-950 p-3 text-xs leading-5">{gitDiff.split('\n').map((line, index) => <span key={index} className={cn('block', line.startsWith('+') && !line.startsWith('+++') && 'bg-green-950/70 text-green-300', line.startsWith('-') && !line.startsWith('---') && 'bg-red-950/70 text-red-300', line.startsWith('@@') && 'text-sky-300')}>{line || ' '}</span>)}</pre> : <p className="p-4 text-sm text-slate-500">No textual changes to display.</p>}{gitDiffTruncated && <p className="border-t border-slate-800 px-3 py-2 text-xs text-amber-400">Diff display was truncated for safety.</p>}</div>}
      </section>}

      {activeProject && <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><TerminalIcon className="h-5 w-5 text-green-500" />Terminal & tests</h2>
            <p className="mt-1 text-sm text-slate-500">Commands are project-scoped, allowlisted, bounded, and require an isolated runtime.</p>
          </div>
          {terminalCapabilities?.test_runner && <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">Detected {terminalCapabilities.test_runner} tests</span>}
        </div>
        {terminalCapabilities && !terminalCapabilities.available && <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-200">{terminalCapabilities.reason} Commands remain disabled until the server has a hardened process sandbox; the API will not run project code directly.</div>}
        {terminalError && <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">{terminalError}</div>}
        <div className="flex flex-col gap-2 sm:flex-row">
          <label htmlFor="coding-terminal-command" className="sr-only">Allowlisted command</label>
          <input id="coding-terminal-command" value={terminalCommand} onChange={event => setTerminalCommand(event.target.value)} onKeyDown={event => { if (event.key === 'Enter') void executeTerminal('command') }} placeholder="Example: npm test" disabled={!terminalCapabilities?.available || terminalRunning} className="min-w-0 flex-1 rounded-lg bg-slate-100 px-3 py-2 font-mono text-sm text-slate-800 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-100" />
          <button onClick={() => void executeTerminal('command')} disabled={!terminalCapabilities?.available || terminalRunning || !terminalCommand.trim()} className="inline-flex items-center justify-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-700"><Play className="h-4 w-4" />Run command</button>
          <button onClick={() => void executeTerminal('tests')} disabled={!terminalCapabilities?.available || !terminalCapabilities.test_runner || terminalRunning} className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"><TestTube2 className="h-4 w-4" />Run tests</button>
          {terminalRunning && <button onClick={() => terminalController.current?.abort()} className="inline-flex items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white"><Square className="h-4 w-4" />Stop</button>}
        </div>
        {terminalRunning && <p role="status" className="flex items-center gap-2 text-sm text-slate-500"><LoaderCircle className="h-4 w-4 animate-spin" />{terminalMode === 'tests' ? 'Running tests…' : 'Command running…'}</p>}
        {terminalResult && <div className="overflow-hidden rounded-xl border border-slate-800">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-300"><code>$ {terminalResult.command}</code><span>{terminalResult.duration_ms} ms · exit {terminalResult.exit_code}</span></div>
          {terminalMode === 'tests' && <p className={cn('px-3 py-2 text-sm font-medium', terminalResult.exit_code === 0 && !terminalResult.timed_out ? 'bg-green-950/60 text-green-300' : 'bg-red-950/60 text-red-300')}>{terminalResult.exit_code === 0 && !terminalResult.timed_out ? '✓ Tests passed' : `✗ Tests failed (exit ${terminalResult.exit_code})`}</p>}
          <pre className="max-h-96 overflow-auto whitespace-pre-wrap break-words bg-slate-950 p-3 text-xs leading-5 text-slate-200">{[terminalResult.stdout, terminalResult.stderr && `STDERR:\n${terminalResult.stderr}`].filter(Boolean).join('\n') || `Process exited with code ${terminalResult.exit_code}`}</pre>
          <p className="border-t border-slate-800 bg-slate-950 px-3 py-2 text-xs text-slate-400">Process exited with code {terminalResult.exit_code}{terminalResult.timed_out ? ' (timed out)' : ''}</p>
          {terminalMode === 'tests' && terminalResult.exit_code !== 0 && <div className="border-t border-slate-800 bg-slate-950 px-3 py-2"><button onClick={askAgentToFixTests} disabled={isLoading || !projectId} className="text-sm font-medium text-sky-300 underline disabled:opacity-50">Ask the coding agent to analyze this failure</button></div>}
        </div>}
      </section>}

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
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code({ inline, className, children, ...props }: any) { const match = /language-(\w+)/.exec(className || ''); const code = String(children).replace(/\n$/, ''); return !inline && match ? <Suspense fallback={<pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-sm text-slate-100">{code}</pre>}><CodeBlock language={match[1]} code={code} onCopy={copy} /></Suspense> : <code className={className} {...props}>{children}</code> } }}>
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

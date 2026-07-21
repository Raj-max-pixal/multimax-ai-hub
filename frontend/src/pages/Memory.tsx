import { useEffect, useState } from 'react'
import { Brain, Plus, Search, Trash2 } from 'lucide-react'
import { createMemory, deleteMemory, getMemories } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

const categories = ['knowledge', 'profile', 'project', 'preference', 'task']

export default function Memory() {
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('knowledge')
  const [tags, setTags] = useState('')
  const [query, setQuery] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [memories, setMemories] = useState<any[]>([])
  const { addToast } = useToast()

  const load = () => getMemories(query, filterCategory).then(data => setMemories(data.memories || [])).catch((e) => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])

  const save = async () => {
    if (!content.trim()) return addToast('Write a memory first', 'error')
    await createMemory({ content, category, tags: tags.split(',').map(t => t.trim()).filter(Boolean) })
    setContent('')
    setTags('')
    addToast('Memory saved', 'success')
    load()
  }

  const remove = async (id: string) => {
    await deleteMemory(id)
    addToast('Memory deleted', 'success')
    load()
  }

  return (
    <div className="space-y-6">
      <div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Memory</h1><p className="text-slate-500 dark:text-slate-400">Project memory, user preferences, tasks, and searchable knowledge.</p></div>
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-1 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100"><Brain className="w-5 h-5 text-green-500" /> Save Memory</div>
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={8} placeholder="Remember this project preference, task, fact, or workflow..." className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{categories.map(c => <option key={c}>{c}</option>)}</select>
          <input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tags comma separated" className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-green-500" />
          <button onClick={save} className="inline-flex items-center gap-2 rounded-xl bg-green-500 px-5 py-2 font-semibold text-white hover:bg-green-600"><Plus className="w-4 h-4" />Save</button>
        </div>
        <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5">
          <div className="flex flex-col md:flex-row gap-3 mb-4">
            <div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" /><input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && load()} placeholder="Search memory..." className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 pl-10 pr-4 py-2 text-slate-800 dark:text-slate-100" /></div>
            <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100"><option value="">All</option>{categories.map(c => <option key={c}>{c}</option>)}</select>
            <button onClick={load} className="rounded-xl bg-green-500 px-4 py-2 font-semibold text-white">Search</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">{memories.map(m => <div key={m.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><div className="flex justify-between gap-3"><span className="text-xs uppercase tracking-wide text-green-500">{m.category}</span><button onClick={() => remove(m.id)} className="text-slate-500 hover:text-red-500"><Trash2 className="w-4 h-4" /></button></div><p className="mt-2 text-slate-800 dark:text-slate-100">{m.content}</p><p className="mt-2 text-xs text-slate-500">{m.tags?.join(', ')}</p></div>)}</div>
        </div>
      </div>
    </div>
  )
}

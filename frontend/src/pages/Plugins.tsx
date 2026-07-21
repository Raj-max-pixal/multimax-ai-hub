import { useEffect, useState } from 'react'
import { Plug, Plus, Store } from 'lucide-react'
import { getPluginCatalog, installPlugin } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function Plugins() {
  const [catalog, setCatalog] = useState<any[]>([])
  const [installed, setInstalled] = useState<any[]>([])
  const { addToast } = useToast()
  const load = () => getPluginCatalog().then(data => { setCatalog(data.catalog || []); setInstalled(data.installed || []) }).catch(e => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])
  const install = async (plugin: any) => { await installPlugin({ ...plugin, enabled: true }); addToast(`${plugin.name} installed`, 'success'); load() }
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Plugin & MCP Marketplace</h1><p className="text-slate-500 dark:text-slate-400">Phase 11: install plugins, MCP servers, integrations, tools, and workflows.</p></div><div className="grid grid-cols-1 lg:grid-cols-3 gap-6"><div className="lg:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 flex gap-2"><Store className="w-5 h-5 text-green-500" />Catalog</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{catalog.map(p => <div key={p.name} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100">{p.name}</p><p className="text-xs uppercase text-green-500">{p.category}</p><p className="my-3 text-sm text-slate-500">{p.description}</p><button onClick={() => install(p)} className="rounded-lg bg-green-500 px-3 py-2 text-sm font-semibold text-white"><Plus className="inline w-4 h-4 mr-1" />Install</button></div>)}</div></div><div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 flex gap-2"><Plug className="w-5 h-5 text-green-500" />Installed</h2><div className="space-y-2">{installed.map(p => <div key={p.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-3"><p className="font-medium text-slate-800 dark:text-slate-100">{p.name}</p><p className="text-xs text-slate-500">{p.category} · {p.enabled ? 'enabled' : 'disabled'}</p></div>)}</div></div></div></div>
}

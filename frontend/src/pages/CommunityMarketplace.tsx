import { useEffect, useState } from 'react'
import { PackagePlus, Store } from 'lucide-react'
import { getMarketplaceItems, publishMarketplaceItem } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function CommunityMarketplace() {
  const [title, setTitle] = useState('Research Agent Prompt Pack')
  const [itemType, setItemType] = useState('prompt')
  const [description, setDescription] = useState('A reusable prompt pack for research workflows.')
  const [content, setContent] = useState('Prompt/template/workflow content...')
  const [items, setItems] = useState<any[]>([])
  const { addToast } = useToast()
  const load = () => getMarketplaceItems().then(d => setItems(d.items || [])).catch(e => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])
  const publish = async () => { await publishMarketplaceItem({ title, item_type: itemType, description, content }); addToast('Published to marketplace', 'success'); load() }
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Community Marketplace</h1><p className="text-slate-500 dark:text-slate-400">Phase 13: publish agents, prompts, templates, plugins, and workflows.</p></div><div className="grid grid-cols-1 xl:grid-cols-3 gap-6"><div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100 flex gap-2"><PackagePlus className="w-5 h-5 text-green-500"/>Publish</h2><input value={title} onChange={e=>setTitle(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100"/><select value={itemType} onChange={e=>setItemType(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['agent','prompt','template','plugin','workflow'].map(x=><option key={x}>{x}</option>)}</select><textarea value={description} onChange={e=>setDescription(e.target.value)} rows={3} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><textarea value={content} onChange={e=>setContent(e.target.value)} rows={6} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><button onClick={publish} className="rounded-xl bg-green-500 px-5 py-2 font-semibold text-white">Publish</button></div><div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 flex gap-2"><Store className="w-5 h-5 text-green-500"/>Items</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{items.map(i=><div key={i.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100">{i.title}</p><p className="text-xs uppercase text-green-500">{i.item_type}</p><p className="text-sm text-slate-500 mt-2">{i.description}</p><p className="text-xs text-slate-500 mt-3">⭐ {i.rating} · {i.downloads} downloads</p></div>)}</div></div></div></div>
}

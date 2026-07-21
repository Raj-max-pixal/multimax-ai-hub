import { useEffect, useState } from 'react'
import { Smartphone, Tablet, Plus } from 'lucide-react'
import { createMobileBuild, getMobileBuilds } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function MobileApps() {
  const [platform, setPlatform] = useState('pwa')
  const [features, setFeatures] = useState('chat, voice, documents, agents, offline shell')
  const [builds, setBuilds] = useState<any[]>([])
  const { addToast } = useToast()
  const load = () => getMobileBuilds().then(d => setBuilds(d.builds || [])).catch(e => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])
  const create = async () => { await createMobileBuild({ platform, app_name: 'Multimax AI Hub', features: features.split(',').map(x=>x.trim()).filter(Boolean) }); addToast('Mobile build plan created', 'success'); load() }
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Mobile Apps</h1><p className="text-slate-500 dark:text-slate-400">Phase 14: Android, iOS, tablet, and PWA planning hub.</p></div><div className="grid grid-cols-1 xl:grid-cols-3 gap-6"><div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100 flex gap-2"><Smartphone className="w-5 h-5 text-green-500"/>Create Build Plan</h2><select value={platform} onChange={e=>setPlatform(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['pwa','android','ios','tablet'].map(x=><option key={x}>{x}</option>)}</select><textarea value={features} onChange={e=>setFeatures(e.target.value)} rows={5} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><button onClick={create} className="rounded-xl bg-green-500 px-5 py-2 font-semibold text-white"><Plus className="inline w-4 h-4 mr-1"/>Create</button></div><div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 flex gap-2"><Tablet className="w-5 h-5 text-green-500"/>Build Plans</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{builds.map(b=><div key={b.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100">{b.app_name}</p><p className="text-xs uppercase text-green-500">{b.platform} · {b.status}</p><p className="text-sm text-slate-500 mt-2">Features: {b.features?.join(', ')}</p><p className="text-sm text-slate-500">Outputs: {b.outputs?.join(', ')}</p></div>)}</div></div></div></div>
}

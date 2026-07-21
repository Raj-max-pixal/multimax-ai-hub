import { useEffect, useState } from 'react'
import { ShieldCheck, Save } from 'lucide-react'
import { getEnterpriseConfig, saveEnterpriseConfig } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function Enterprise() {
  const [feature, setFeature] = useState('audit')
  const [enabled, setEnabled] = useState(true)
  const [notes, setNotes] = useState('Enable enterprise-grade controls for production deployment.')
  const [configs, setConfigs] = useState<any[]>([])
  const { addToast } = useToast()
  const load = () => getEnterpriseConfig().then(d => setConfigs(d.configs || [])).catch(e => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])
  const save = async () => { await saveEnterpriseConfig({ feature, enabled, notes }); addToast('Enterprise config saved', 'success'); load() }
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Enterprise Platform</h1><p className="text-slate-500 dark:text-slate-400">Phase 15: SSO, audit logs, cloud deployment, RBAC, and enterprise APIs.</p></div><div className="grid grid-cols-1 xl:grid-cols-3 gap-6"><div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100 flex gap-2"><ShieldCheck className="w-5 h-5 text-green-500"/>Configure</h2><select value={feature} onChange={e=>setFeature(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100">{['sso','audit','rbac','cloud','api'].map(x=><option key={x}>{x}</option>)}</select><label className="flex items-center gap-2 text-slate-700 dark:text-slate-200"><input type="checkbox" checked={enabled} onChange={e=>setEnabled(e.target.checked)} /> Enabled</label><textarea value={notes} onChange={e=>setNotes(e.target.value)} rows={6} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><button onClick={save} className="rounded-xl bg-green-500 px-5 py-2 font-semibold text-white"><Save className="inline w-4 h-4 mr-1"/>Save</button></div><div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Enterprise Controls</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{configs.map(c=><div key={c.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100 uppercase">{c.feature}</p><p className="text-xs text-green-500">{c.enabled ? 'enabled' : 'disabled'}</p><p className="text-sm text-slate-500 mt-2">{c.notes}</p></div>)}</div></div></div></div>
}

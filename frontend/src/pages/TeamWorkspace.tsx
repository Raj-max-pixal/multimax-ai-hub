import { useEffect, useState } from 'react'
import { Users, Plus } from 'lucide-react'
import { createTeamWorkspace, getTeamWorkspaces } from '../lib/api'
import { useToast } from '../contexts/ToastContext'

export default function TeamWorkspace() {
  const [name, setName] = useState('Multimax Team')
  const [members, setMembers] = useState('raj@example.com, developer@example.com')
  const [permissions, setPermissions] = useState('shared chats, shared agents, team folders')
  const [workspaces, setWorkspaces] = useState<any[]>([])
  const { addToast } = useToast()
  const load = () => getTeamWorkspaces().then(d => setWorkspaces(d.workspaces || [])).catch(e => addToast(e.message, 'error'))
  useEffect(() => { load() }, [])
  const create = async () => { await createTeamWorkspace({ name, members: members.split(',').map(x => x.trim()).filter(Boolean), permissions: permissions.split(',').map(x => x.trim()).filter(Boolean) }); addToast('Team workspace created', 'success'); load() }
  return <div className="space-y-6"><div><h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100">Team Workspace</h1><p className="text-slate-500 dark:text-slate-400">Phase 12: organizations, shared chats, agents, folders, and permissions.</p></div><div className="grid grid-cols-1 xl:grid-cols-3 gap-6"><div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"><h2 className="font-semibold text-slate-800 dark:text-slate-100 flex gap-2"><Users className="w-5 h-5 text-green-500" />Create Workspace</h2><input value={name} onChange={e=>setName(e.target.value)} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 px-4 py-2 text-slate-800 dark:text-slate-100"/><textarea value={members} onChange={e=>setMembers(e.target.value)} rows={3} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><textarea value={permissions} onChange={e=>setPermissions(e.target.value)} rows={3} className="w-full rounded-xl bg-slate-100 dark:bg-slate-800 p-4 text-slate-800 dark:text-slate-100"/><button onClick={create} className="rounded-xl bg-green-500 px-5 py-2 font-semibold text-white"><Plus className="inline w-4 h-4 mr-1"/>Create</button></div><div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5"><h2 className="font-semibold text-slate-800 dark:text-slate-100 mb-4">Workspaces</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{workspaces.map(w=><div key={w.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4"><p className="font-semibold text-slate-800 dark:text-slate-100">{w.name}</p><p className="text-sm text-slate-500 mt-2">Members: {w.members?.join(', ')}</p><p className="text-sm text-slate-500">Permissions: {w.permissions?.join(', ')}</p></div>)}</div></div></div></div>
}

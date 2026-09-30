import { useEffect, useState } from 'react'
import { Camera, Mail, Shield, User } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const profileSchema = z.object({
  username: z.string().trim().min(3, 'Username must be at least 3 characters').max(100).regex(/^[a-zA-Z0-9_.-]+$/, 'Use letters, numbers, dots, underscores, or hyphens'),
  displayName: z.string().trim().min(2, 'Name must be at least 2 characters').max(255),
  bio: z.string().trim().max(160, 'About must be 160 characters or fewer'),
  avatarUrl: z.string().trim().max(512, 'Photo URL is too long').refine((value) => !value || /^https?:\/\//i.test(value), 'Enter an http or https image URL'),
})

type ProfileFormData = z.infer<typeof profileSchema>

const fieldClass = 'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-green-500 focus:ring-2 focus:ring-green-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100'

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const { addToast } = useToast()
  const [isEditing, setIsEditing] = useState(false)
  const [avatarFailed, setAvatarFailed] = useState(false)

  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      username: user?.username || '',
      displayName: user?.display_name || '',
      bio: user?.bio || '',
      avatarUrl: user?.avatar_url || '',
    },
  })

  useEffect(() => {
    reset({
      username: user?.username || '',
      displayName: user?.display_name || '',
      bio: user?.bio || '',
      avatarUrl: user?.avatar_url || '',
    })
    setAvatarFailed(false)
  }, [user, reset])

  const avatarUrl = watch('avatarUrl')
  const savedAvatar = user?.avatar_url
  const avatar = isEditing ? avatarUrl : savedAvatar
  const avatarLetter = user?.display_name?.charAt(0) || user?.username?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase() || 'U'

  const onSubmit = async (data: ProfileFormData) => {
    try {
      await updateProfile({
        username: data.username,
        display_name: data.displayName,
        bio: data.bio,
        avatar_url: data.avatarUrl,
      })
      setIsEditing(false)
      addToast('Profile updated', 'success')
    } catch (error) {
      addToast(error instanceof Error ? error.message : 'Failed to update profile', 'error')
    }
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6">
      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="h-28 bg-gradient-to-r from-green-500/20 via-emerald-400/10 to-cyan-500/20" />
        <div className="px-6 pb-7 sm:px-8">
          <div className="-mt-12 flex flex-wrap items-end justify-between gap-4">
            <div className="flex items-end gap-4">
              <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border-4 border-white bg-gradient-to-br from-green-400 to-green-600 text-3xl font-bold text-white dark:border-slate-900">
                {avatar && !avatarFailed ? <img src={avatar} alt="Profile" className="h-full w-full object-cover" onError={() => setAvatarFailed(true)} /> : avatarLetter}
              </div>
              <div className="pb-1">
                <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{user?.display_name || user?.username || 'Your profile'}</h1>
                <p className="text-slate-500 dark:text-slate-400">@{user?.username || 'username'}</p>
              </div>
            </div>
            {!isEditing && <button type="button" onClick={() => setIsEditing(true)} className="rounded-xl border border-slate-300 px-4 py-2 font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800">Edit profile</button>}
          </div>

          {isEditing ? (
            <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Username</span>
                <div className="flex items-center rounded-xl border border-slate-300 bg-white px-4 dark:border-slate-700 dark:bg-slate-950"><span className="text-slate-400">@</span><input {...register('username')} className="w-full border-0 bg-transparent px-2 py-3 text-slate-900 outline-none dark:text-slate-100" autoComplete="username" /></div>
                {errors.username && <span className="text-sm text-red-500">{errors.username.message}</span>}
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Name</span>
                <input {...register('displayName')} className={fieldClass} autoComplete="name" />
                {errors.displayName && <span className="text-sm text-red-500">{errors.displayName.message}</span>}
              </label>
              <label className="block space-y-1.5">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">About</span>
                <textarea {...register('bio')} rows={3} maxLength={160} placeholder="A little about you" className={`${fieldClass} resize-y`} />
                <span className="flex justify-between text-xs text-slate-500"><span>{errors.bio?.message}</span><span>{(watch('bio') || '').length}/160</span></span>
              </label>
              <label className="block space-y-1.5">
                <span className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300"><Camera className="h-4 w-4" />Profile photo URL</span>
                <input {...register('avatarUrl')} type="url" placeholder="https://example.com/photo.jpg" className={fieldClass} />
                {errors.avatarUrl && <span className="text-sm text-red-500">{errors.avatarUrl.message}</span>}
                <span className="block text-xs text-slate-500">Use a public image URL. Direct photo uploads need configured image storage.</span>
              </label>
              <div className="flex gap-3 pt-1">
                <button type="submit" disabled={isSubmitting} className="rounded-xl bg-green-600 px-5 py-2.5 font-semibold text-white transition hover:bg-green-700 disabled:cursor-wait disabled:opacity-60">{isSubmitting ? 'Saving…' : 'Save changes'}</button>
                <button type="button" disabled={isSubmitting} onClick={() => { reset(); setAvatarFailed(false); setIsEditing(false) }} className="rounded-xl bg-slate-100 px-5 py-2.5 font-medium text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700">Cancel</button>
              </div>
            </form>
          ) : (
            <div className="mt-7 space-y-6">
              {user?.bio && <p className="whitespace-pre-wrap text-slate-700 dark:text-slate-300">{user.bio}</p>}
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/70"><div className="mb-2 flex items-center gap-2 text-sm text-slate-500"><User className="h-4 w-4" />Username</div><p className="font-medium text-slate-900 dark:text-slate-100">@{user?.username || 'Not set'}</p></div>
                <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/70"><div className="mb-2 flex items-center gap-2 text-sm text-slate-500"><Mail className="h-4 w-4" />Email</div><p className="break-all font-medium text-slate-900 dark:text-slate-100">{user?.email}</p></div>
                <div className="rounded-xl bg-slate-50 p-4 dark:bg-slate-800/70"><div className="mb-2 flex items-center gap-2 text-sm text-slate-500"><Shield className="h-4 w-4" />Account</div><p className="font-medium capitalize text-slate-900 dark:text-slate-100">{user?.role || 'user'}</p></div>
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  )
}

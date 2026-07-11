import { useState } from 'react'
import { User, Mail } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../contexts/ToastContext'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const profileSchema = z.object({
  fullName: z.string().min(2, 'Name must be at least 2 characters')
})

type ProfileFormData = z.infer<typeof profileSchema>

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const { addToast } = useToast()
  const [isEditing, setIsEditing] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors }
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      fullName: user?.full_name || ''
    }
  })

  const onSubmit = async (data: ProfileFormData) => {
    try {
      await updateProfile({ full_name: data.fullName })
      setIsEditing(false)
      addToast('Profile updated!', 'success')
    } catch (error: any) {
      addToast(error.message || 'Failed to update profile', 'error')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8">
        <div className="flex items-center gap-6 mb-8">
          <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center text-4xl font-bold text-white">
            {user?.full_name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {user?.full_name || 'User'}
            </h1>
            <p className="text-slate-500 dark:text-slate-400 flex items-center gap-2">
              <Mail className="w-4 h-4" />
              {user?.email}
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-xl">
              <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 mb-2">
                <User className="w-5 h-5" />
                <span className="text-sm font-medium">Full Name</span>
              </div>
              {isEditing ? (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
                  <input
                    {...register('fullName')}
                    className="w-full px-4 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-slate-800 dark:text-slate-100"
                  />
                  {errors.fullName && (
                    <p className="text-sm text-red-500">{errors.fullName.message}</p>
                  )}
                  <div className="flex gap-3">
                    <button
                      type="submit"
                      className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                    >
                      Save
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditing(false)
                        reset()
                      }}
                      className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex items-center justify-between">
                  <p className="text-slate-800 dark:text-slate-100 font-medium">
                    {user?.full_name || 'Not set'}
                  </p>
                  <button
                    onClick={() => setIsEditing(true)}
                    className="text-sm text-green-600 dark:text-green-400 hover:underline"
                  >
                    Edit
                  </button>
                </div>
              )}
            </div>

            <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-xl">
              <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400 mb-2">
                <Mail className="w-5 h-5" />
                <span className="text-sm font-medium">Email</span>
              </div>
              <p className="text-slate-800 dark:text-slate-100 font-medium">
                {user?.email}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

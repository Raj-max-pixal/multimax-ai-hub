import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { User } from '../types'
import { Session } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (email: string, password: string, fullName: string) => Promise<{ error: Error | null }>
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>
  signInWithGoogle: () => Promise<void>
  signInWithGitHub: () => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<{ error: Error | null }>
  updateProfile: (data: Partial<User>) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>({
    id: 'demo-user',
    email: 'demo@multimax.ai',
    full_name: 'Demo User'
  })
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (supabase) {
      const init = async () => {
        setLoading(true)
        const { data: { session } } = await supabase!.auth.getSession()
        setSession(session)
        if (session?.user) {
          setUser({
            id: session.user.id,
            email: session.user.email!,
            avatar_url: session.user.user_metadata.avatar_url,
            full_name: session.user.user_metadata.full_name,
          })
        }

        const { data: { subscription } } = supabase!.auth.onAuthStateChange(
          (_event, session) => {
            setSession(session)
            if (session?.user) {
              setUser({
                id: session.user.id,
                email: session.user.email!,
                avatar_url: session.user.user_metadata.avatar_url,
                full_name: session.user.user_metadata.full_name,
              })
            } else {
              setUser({
                id: 'demo-user',
                email: 'demo@multimax.ai',
                full_name: 'Demo User'
              })
            }
            setLoading(false)
          }
        )
        
        setLoading(false)

        return () => subscription.unsubscribe()
      }
      init()
    }
  }, [])

  const signUp = async (email: string, password: string, fullName: string) => {
    if (!supabase) {
      setUser({
        id: 'demo-user',
        email,
        full_name: fullName
      })
      return { error: null }
    }
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName } },
    })
    return { error }
  }

  const signIn = async (email: string, password: string) => {
    if (!supabase) {
      setUser({
        id: 'demo-user',
        email,
        full_name: 'Demo User'
      })
      return { error: null }
    }
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    return { error }
  }

  const signInWithGoogle = async () => {
    if (!supabase) {
      setUser({
        id: 'demo-user',
        email: 'demo@multimax.ai',
        full_name: 'Google User'
      })
      return
    }
    await supabase.auth.signInWithOAuth({ provider: 'google' })
  }

  const signInWithGitHub = async () => {
    if (!supabase) {
      setUser({
        id: 'demo-user',
        email: 'demo@multimax.ai',
        full_name: 'GitHub User'
      })
      return
    }
    await supabase.auth.signInWithOAuth({ provider: 'github' })
  }

  const signOut = async () => {
    if (supabase) {
      await supabase.auth.signOut()
    }
    setUser({
      id: 'demo-user',
      email: 'demo@multimax.ai',
      full_name: 'Demo User'
    })
  }

  const resetPassword = async (email: string) => {
    if (!supabase) {
      return { error: null }
    }
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    return { error }
  }

  const updateProfile = async (data: Partial<User>) => {
    if (supabase && user?.id) {
      await supabase.auth.updateUser({ data })
    }
    setUser(prev => prev ? { ...prev, ...data } : null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        signUp,
        signIn,
        signInWithGoogle,
        signInWithGitHub,
        signOut,
        resetPassword,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

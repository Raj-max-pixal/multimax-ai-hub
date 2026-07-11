import { createContext, useContext, useEffect, useState, useCallback } from 'react'
  import {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentUser,
  updateCurrentUser as updateUserApi,
  resetPassword as resetPasswordApi,
  updatePassword as updatePasswordApi,
  type UserProfile,
} from '../lib/auth-api'
import { setOnRefreshFailed, clearTokens, getAccessToken } from '../lib/api-client'

// ------------------------------------------------------------------ //
// Types
// ------------------------------------------------------------------ //

export interface AuthUser {
  id: string
  email: string
  username: string
  display_name: string
  role: string
  is_active: boolean
  is_verified: boolean
  avatar_url: string
}

interface AuthContextType {
  user: AuthUser | null
  loading: boolean
  signIn: (username: string, password: string) => Promise<{ error: Error | null }>
  signUp: (email: string, username: string, password: string, display_name?: string) => Promise<{ error: Error | null }>
  signOut: () => Promise<void>
  updateProfile: (data: Partial<AuthUser>) => Promise<void>
  resetPassword: (email: string) => Promise<{ error: Error | null }>
  updatePassword: (token: string, password: string) => Promise<{ error: Error | null }>
}

// ------------------------------------------------------------------ //
// Context
// ------------------------------------------------------------------ //

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function mapProfileToUser(p: UserProfile): AuthUser {
  return {
    id: p.id,
    email: p.email,
    username: p.username,
    display_name: p.display_name,
    role: p.role,
    is_active: p.is_active,
    is_verified: p.is_verified,
    avatar_url: p.avatar_url,
  }
}

// ------------------------------------------------------------------ //
// Provider
// ------------------------------------------------------------------ //

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  // ------------------------------------------------------------------ //
  // On mount: check if we have a stored token, try to restore session
  // ------------------------------------------------------------------ //
  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setLoading(false)
      return
    }

    let cancelled = false

    ;(async () => {
      try {
        const profile = await getCurrentUser()
        if (!cancelled) {
          setUser(mapProfileToUser(profile))
        }
      } catch {
        // Token invalid or expired — clear it
        clearTokens()
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [])

  // ------------------------------------------------------------------ //
  // Register a global handler for refresh failures
  // ------------------------------------------------------------------ //
  useEffect(() => {
    setOnRefreshFailed(() => {
      setUser(null)
    })
  }, [])

  // ------------------------------------------------------------------ //
  // signIn
  // ------------------------------------------------------------------ //
  const signIn = useCallback(async (username: string, password: string) => {
    try {
      const data = await loginUser(username, password)
      setUser(mapProfileToUser(data.user))
      return { error: null }
    } catch (err: any) {
      return { error: err instanceof Error ? err : new Error(String(err)) }
    }
  }, [])

  // ------------------------------------------------------------------ //
  // signUp
  // ------------------------------------------------------------------ //
  const signUp = useCallback(
    async (email: string, username: string, password: string, display_name?: string) => {
      try {
        await registerUser(email, username, password, display_name)
        // Don't auto-login — user must verify email first (if verification is on)
        // Or we could auto-login them. For now, just return success.
        return { error: null }
      } catch (err: any) {
        return { error: err instanceof Error ? err : new Error(String(err)) }
      }
    },
    [],
  )

  // ------------------------------------------------------------------ //
  // signOut
  // ------------------------------------------------------------------ //
  const signOut = useCallback(async () => {
    await logoutUser()
    setUser(null)
  }, [])

  // ------------------------------------------------------------------ //
  // updateProfile
  // ------------------------------------------------------------------ //
  const updateProfile = useCallback(async (data: Partial<AuthUser>) => {
    try {
      const updated = await updateUserApi({
        display_name: data.display_name,
        avatar_url: data.avatar_url,
      })
      setUser(mapProfileToUser(updated))
    } catch (err) {
      console.error('Failed to update profile:', err)
    }
  }, [])

  // ------------------------------------------------------------------ //
  // resetPassword
  // ------------------------------------------------------------------ //
  const resetPassword = useCallback(async (email: string) => {
    try {
      await resetPasswordApi(email)
      return { error: null }
    } catch (err: any) {
      return { error: err instanceof Error ? err : new Error(String(err)) }
    }
  }, [])

  // ------------------------------------------------------------------ //
  // updatePassword
  // ------------------------------------------------------------------ //
  const updatePassword = useCallback(async (token: string, password: string) => {
    try {
      await updatePasswordApi(token, password)
      return { error: null }
    } catch (err: any) {
      return { error: err instanceof Error ? err : new Error(String(err)) }
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn,
        signUp,
        signOut,
        updateProfile,
        resetPassword,
        updatePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// ------------------------------------------------------------------ //
// Hook
// ------------------------------------------------------------------ //

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
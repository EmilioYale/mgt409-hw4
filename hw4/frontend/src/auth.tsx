import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, tokenStore } from './api'
import type { User } from './types'

interface AuthState {
  user: User | null
  ready: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (body: { first_name: string; last_name: string; email: string; password: string }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!tokenStore.get()) {
      setReady(true)
      return
    }
    api
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear()) // expired or revoked session
      .finally(() => setReady(true))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.login(email, password)
    tokenStore.set(res.token)
    setUser(res.user)
  }, [])

  const signup = useCallback(async (body: Parameters<AuthState['signup']>[0]) => {
    const res = await api.signup(body)
    tokenStore.set(res.token)
    setUser(res.user)
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } finally {
      tokenStore.clear()
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, ready, login, signup, logout }), [user, ready, login, signup, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}

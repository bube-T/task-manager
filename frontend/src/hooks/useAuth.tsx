import { createContext, useContext, useEffect, useState } from 'react'
import type { User } from '../types'
import { getMe } from '../api/auth'

interface AuthCtx {
  user: User | null
  token: string | null
  setToken: (t: string | null) => void
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const setToken = (t: string | null) => {
    setTokenState(t)
    if (t) localStorage.setItem('token', t)
    else localStorage.removeItem('token')
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    getMe()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false))
  }, [token])

  return (
    <AuthContext.Provider value={{ user, token, setToken, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

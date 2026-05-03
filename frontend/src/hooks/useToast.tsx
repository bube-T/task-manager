import { createContext, useContext, useState, useCallback } from 'react'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error'
}

interface ToastCtx {
  toasts: Toast[]
  success: (msg: string) => void
  error: (msg: string) => void
  dismiss: (id: number) => void
}

const ToastContext = createContext<ToastCtx>({} as ToastCtx)

let nextId = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const add = useCallback((message: string, type: Toast['type']) => {
    const id = ++nextId
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500)
  }, [])

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, success: (m) => add(m, 'success'), error: (m) => add(m, 'error'), dismiss }}>
      {children}
    </ToastContext.Provider>
  )
}

export const useToast = () => useContext(ToastContext)

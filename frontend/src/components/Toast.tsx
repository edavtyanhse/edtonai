import { useState, useCallback, ReactNode, useContext } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'
import { ToastContext, type ToastType } from '@/context/ToastContext'

interface Toast {
  id: number
  type: ToastType
  message: string
}

let toastId = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const showToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastId
    setToasts((prev) => [...prev, { id, type, message }])

    // Auto remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const icons = {
    success: <CheckCircle className="w-5 h-5 text-app-success" />,
    error: <AlertCircle className="w-5 h-5 text-app-danger" />,
    info: <Info className="w-5 h-5 text-app-accent" />,
  }

  const backgrounds = {
    success: 'bg-app-success-soft border-app-success/30',
    error: 'bg-app-danger-soft border-app-danger/30',
    info: 'bg-app-accent-soft border-app-accent/30',
  }

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg min-w-[300px] max-w-md animate-slide-in ${backgrounds[toast.type]}`}
    >
      {icons[toast.type]}
      <span className="flex-1 text-sm text-app-text-muted">{toast.message}</span>
      <button onClick={onClose} className="text-app-text-subtle hover:text-app-text-muted">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return context
}

// Standalone Toaster component that can be used without context
export function Toaster() {
  return <ToastProvider>{null}</ToastProvider>
}

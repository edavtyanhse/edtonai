import { type ToastType } from '@/context/ToastContext'

// Global toast function for use outside React components
let globalShowToast: ((type: ToastType, message: string) => void) | null = null

export function setGlobalToast(fn: (type: ToastType, message: string) => void) {
  globalShowToast = fn
}

export function toast(type: ToastType, message: string) {
  globalShowToast?.(type, message)
}

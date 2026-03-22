import { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import { refreshTokenApi, logoutApi, type UserResponse } from '@/api/auth'
import { setAccessToken, clearTokens } from '@/lib/auth'

interface AuthContextType {
    user: UserResponse | null
    loading: boolean
    signOut: () => Promise<void>
    /** Call after login/register to set user + token from AuthResponse */
    setAuth: (accessToken: string, user: UserResponse) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<UserResponse | null>(null)
    const [loading, setLoading] = useState(true)
    const refreshTimerRef = useRef<ReturnType<typeof setTimeout>>()

    const scheduleRefresh = useCallback((expiresIn: number) => {
        if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        // Refresh 60 seconds before expiry
        const delay = Math.max((expiresIn - 60) * 1000, 10_000)
        refreshTimerRef.current = setTimeout(async () => {
            try {
                const data = await refreshTokenApi()
                setAccessToken(data.access_token)
                setUser(data.user)
                scheduleRefresh(data.expires_in)
            } catch {
                // Refresh failed — session expired
                clearTokens()
                setUser(null)
            }
        }, delay)
    }, [])

    // On mount: try to refresh (cookie may still be valid)
    useEffect(() => {
        let cancelled = false
        refreshTokenApi()
            .then((data) => {
                if (cancelled) return
                setAccessToken(data.access_token)
                setUser(data.user)
                scheduleRefresh(data.expires_in)
            })
            .catch(() => {
                // No valid refresh token — user not logged in
            })
            .finally(() => {
                if (!cancelled) setLoading(false)
            })

        return () => {
            cancelled = true
            if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        }
    }, [scheduleRefresh])

    const signOut = useCallback(async () => {
        if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        try {
            await logoutApi()
        } catch { /* ignore */ }
        clearTokens()
        setUser(null)
    }, [])

    const setAuth = useCallback((accessToken: string, userData: UserResponse) => {
        setAccessToken(accessToken)
        setUser(userData)
    }, [])

    return (
        <AuthContext.Provider value={{ user, loading, signOut, setAuth }}>
            {children}
        </AuthContext.Provider>
    )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}

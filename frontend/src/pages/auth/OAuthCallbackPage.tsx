import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, XCircle } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { setAccessToken } from '@/lib/auth'
import { Button } from '@/components'

export default function OAuthCallbackPage() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const { setAuth } = useAuth()
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const accessToken = searchParams.get('access_token')
        const refreshToken = searchParams.get('refresh_token')
        const errorMsg = searchParams.get('error')

        if (errorMsg) {
            setError(errorMsg)
            return
        }

        if (!accessToken) {
            setError('No access token received')
            return
        }

        // Clear tokens from URL immediately
        window.history.replaceState({}, '', '/oauth/callback')

        // 1. Set access token in memory
        setAccessToken(accessToken)

        // 2. Store refresh token as httpOnly cookie via backend
        const storeRefreshAndAuth = async () => {
            try {
                if (refreshToken) {
                    await fetch(`/api/auth/set-cookie?refresh_token=${encodeURIComponent(refreshToken)}`, {
                        method: 'POST',
                        credentials: 'include',
                    })
                }

                // 3. Fetch user info
                const res = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${accessToken}` },
                })
                if (!res.ok) throw new Error('Failed to get user info')
                const user = await res.json()

                setAuth(accessToken, user)
                navigate('/', { replace: true })
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Authentication failed')
            }
        }

        storeRefreshAndAuth()
    }, []) // eslint-disable-line react-hooks/exhaustive-deps

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
                <div className="max-w-md w-full bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700 text-center space-y-4">
                    <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto border border-red-500/30">
                        <XCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">Authentication Failed</h2>
                    <p className="text-slate-400">{error}</p>
                    <Button onClick={() => navigate('/login')} className="w-full">
                        Back to Login
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
    )
}

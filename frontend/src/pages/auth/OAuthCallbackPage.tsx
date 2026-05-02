import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, XCircle } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { refreshTokenApi } from '@/api/auth'
import { Button } from '@/components'

export default function OAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setAuth } = useAuth()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const errorMsg = searchParams.get('error')

    if (errorMsg) {
      setError(errorMsg)
      return
    }

    window.history.replaceState({}, '', '/oauth/callback')

    const refreshAndAuth = async () => {
      try {
        const data = await refreshTokenApi()
        setAuth(data.access_token, data.user)
        navigate('/', { replace: true })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Authentication failed')
      }
    }

    refreshAndAuth()
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

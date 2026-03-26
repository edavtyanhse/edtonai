import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Loader2, LogIn } from 'lucide-react'
import { loginApi } from '@/api/auth'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components'

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [emailNotVerified, setEmailNotVerified] = useState(false)
    const navigate = useNavigate()
    const { setAuth } = useAuth()

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setEmailNotVerified(false)

        try {
            const data = await loginApi(email, password)
            setAuth(data.access_token, data.user)
            navigate('/')
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Error logging in'
            if (message.toLowerCase().includes('email not verified')) {
                setEmailNotVerified(true)
            } else {
                setError(message)
            }
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
            <div className="max-w-md w-full space-y-8 bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700">
                <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/20 mx-auto mb-4">
                        <span className="text-white font-bold text-2xl">E</span>
                    </div>
                    <h2 className="text-3xl font-bold text-white">Welcome back</h2>
                    <p className="mt-2 text-slate-400">Sign in to your EdTon account</p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    {emailNotVerified && (
                        <div className="bg-amber-900/30 text-amber-300 p-3 rounded-lg text-sm border border-amber-500/30">
                            Please verify your email before signing in. Check your inbox for the verification link.
                        </div>
                    )}
                    {error && (
                        <div className="bg-red-900/30 text-red-300 p-3 rounded-lg text-sm border border-red-500/30">
                            {error}
                        </div>
                    )}

                    <div className="space-y-4">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-300">
                                Email
                            </label>
                            <input
                                id="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-slate-600 rounded-lg bg-slate-900 text-white placeholder-slate-500 focus:ring-brand-500 focus:border-brand-500"
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-slate-600 rounded-lg bg-slate-900 text-white placeholder-slate-500 focus:ring-brand-500 focus:border-brand-500"
                            />
                        </div>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <LogIn className="w-4 h-4 mr-2" />}
                        Sign In
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-slate-700" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-slate-800 px-2 text-slate-500">or continue with</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3">
                        <a
                            href="/api/auth/oauth/google"
                            className="flex items-center justify-center px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            Google
                        </a>
                        <a
                            href="/api/auth/oauth/vk"
                            className="flex items-center justify-center px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            VK
                        </a>
                        <a
                            href="/api/auth/oauth/yandex"
                            className="flex items-center justify-center px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            Yandex
                        </a>
                    </div>

                    <p className="text-center text-sm text-slate-400">
                        Don't have an account?{' '}
                        <Link to="/register" className="font-medium text-brand-400 hover:text-brand-300">
                            Sign up
                        </Link>
                    </p>
                </form>
            </div>
        </div>
    )
}

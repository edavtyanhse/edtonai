import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, UserPlus, Mail } from 'lucide-react'
import { registerApi } from '@/api/auth'
import { Button } from '@/components'

export default function RegisterPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [registered, setRegistered] = useState(false)

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            await registerApi(email, password)
            setRegistered(true)
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Error registering')
        } finally {
            setLoading(false)
        }
    }

    if (registered) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
                <div className="max-w-md w-full bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700 text-center space-y-4">
                    <div className="w-16 h-16 bg-brand-900/30 rounded-full flex items-center justify-center mx-auto border border-brand-500/30">
                        <Mail className="w-8 h-8 text-brand-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">Check your email</h2>
                    <p className="text-slate-400">
                        We sent a verification link to <span className="text-white font-medium">{email}</span>.
                        Please check your inbox and click the link to activate your account.
                    </p>
                    <div className="pt-4">
                        <Link to="/login">
                            <Button className="w-full">Go to Login</Button>
                        </Link>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
            <div className="max-w-md w-full space-y-8 bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700">
                <div className="text-center">
                    <div className="w-16 h-16 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/20 mx-auto mb-4">
                        <span className="text-white font-bold text-2xl">E</span>
                    </div>
                    <h2 className="text-3xl font-bold text-white">Create Account</h2>
                    <p className="mt-2 text-slate-400">Start creating better resumes today</p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleRegister}>
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
                                minLength={8}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-1 block w-full px-3 py-2 border border-slate-600 rounded-lg bg-slate-900 text-white placeholder-slate-500 focus:ring-brand-500 focus:border-brand-500"
                            />
                            <p className="text-xs text-slate-500 mt-1">Min. 8 characters</p>
                        </div>
                    </div>

                    <Button type="submit" disabled={loading} className="w-full">
                        {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <UserPlus className="w-4 h-4 mr-2" />}
                        Sign Up
                    </Button>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center">
                            <span className="w-full border-t border-slate-700" />
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-slate-800 px-2 text-slate-500">or continue with</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <a
                            href="/api/auth/oauth/google"
                            className="flex items-center justify-center px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            Google
                        </a>
                        <a
                            href="/api/auth/oauth/yandex"
                            className="flex items-center justify-center px-4 py-2 border border-slate-600 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            Yandex
                        </a>
                    </div>

                    <p className="text-center text-sm text-slate-400">
                        Already have an account?{' '}
                        <Link to="/login" className="font-medium text-brand-400 hover:text-brand-300">
                            Sign in
                        </Link>
                    </p>
                </form>
            </div>
        </div>
    )
}

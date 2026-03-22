import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { verifyEmailApi } from '@/api/auth'
import { Button } from '@/components'

export default function VerifyEmailPage() {
    const [searchParams] = useSearchParams()
    const token = searchParams.get('token')
    const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
    const [message, setMessage] = useState('')

    useEffect(() => {
        if (!token) {
            setStatus('error')
            setMessage('Verification token is missing')
            return
        }

        verifyEmailApi(token)
            .then(() => {
                setStatus('success')
                setMessage('Email verified successfully!')
            })
            .catch((err) => {
                setStatus('error')
                setMessage(err instanceof Error ? err.message : 'Verification failed')
            })
    }, [token])

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-900 px-4">
            <div className="max-w-md w-full bg-slate-800 p-8 rounded-xl shadow-lg border border-slate-700 text-center space-y-4">
                {status === 'loading' && (
                    <>
                        <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto" />
                        <h2 className="text-xl font-bold text-white">Verifying email...</h2>
                    </>
                )}
                {status === 'success' && (
                    <>
                        <div className="w-16 h-16 bg-green-900/30 rounded-full flex items-center justify-center mx-auto border border-green-500/30">
                            <CheckCircle className="w-8 h-8 text-green-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">{message}</h2>
                        <p className="text-slate-400">You can now sign in to your account.</p>
                    </>
                )}
                {status === 'error' && (
                    <>
                        <div className="w-16 h-16 bg-red-900/30 rounded-full flex items-center justify-center mx-auto border border-red-500/30">
                            <XCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <h2 className="text-2xl font-bold text-white">Verification Failed</h2>
                        <p className="text-slate-400">{message}</p>
                    </>
                )}
                <div className="pt-4">
                    <Link to="/login">
                        <Button className="w-full">Go to Login</Button>
                    </Link>
                </div>
            </div>
        </div>
    )
}

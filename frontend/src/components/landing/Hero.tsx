import React from 'react'
import { motion } from 'framer-motion'
import { FileText, CheckCircle, RefreshCw, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Language } from './types'

interface HeroProps {
  lang: Language
}

const Hero: React.FC<HeroProps> = ({ lang }) => {
  const content = {
    en: {
      title: (
        <>
          Get Hired Faster with{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-indigo-400">
            AI-Adapted
          </span>{' '}
          Resumes
        </>
      ),
      description:
        'Stop guessing what recruiters want. Our AI analyzes job descriptions and instantly rewrites your resume to pass ATS filters and land more interviews.',
      ctaPrimary: 'Optimize My Resume',
      ctaSecondary: 'Ideal Resume',
      matchScore: '98% Match',
    },
    ru: {
      title: (
        <>
          Найди работу быстрее с{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-indigo-400">
            AI-Резюме
          </span>
        </>
      ),
      description:
        'Перестаньте гадать, чего хотят рекрутеры. Наш ИИ анализирует вакансии и мгновенно переписывает ваше резюме, чтобы пройти ATS фильтры и получить больше приглашений.',
      ctaPrimary: 'Оптимизировать резюме',
      ctaSecondary: 'Идеальное резюме',
      matchScore: '98% Совпадение',
    },
  }

  const t = content[lang]

  return (
    <section className="relative w-full min-h-screen flex items-center justify-center pt-24 pb-12 px-4 sm:px-6 lg:px-8 overflow-hidden bg-slate-900">
      {/* Background Blobs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="container mx-auto relative z-10 grid lg:grid-cols-2 gap-12 items-center">
        {/* Left Content */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center lg:text-left"
        >
          <h1 className="text-5xl lg:text-7xl font-extrabold tracking-tight text-white leading-tight mb-6">
            {t.title}
          </h1>
          <p className="text-lg text-slate-400 mb-8 max-w-2xl mx-auto lg:mx-0">{t.description}</p>
          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
            <Link
              to="/wizard"
              className="px-8 py-4 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-lg transition-all shadow-lg shadow-brand-500/25 flex items-center gap-2 group"
            >
              {t.ctaPrimary}
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/ideal-resume"
              className="px-8 py-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-lg border border-slate-700 transition-all flex items-center gap-2"
            >
              {t.ctaSecondary}
            </Link>
          </div>
        </motion.div>

        {/* Right Visual - Animated Resume Sync */}
        <motion.div
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="relative h-[500px] w-full hidden lg:block"
        >
          {/* Resume Card */}
          <motion.div
            className="absolute left-0 top-10 w-72 h-96 bg-white rounded-xl shadow-2xl p-6 z-10 border border-slate-200"
            initial={{ rotate: -5 }}
            animate={{ rotate: -2 }}
            transition={{ duration: 6, repeat: Infinity, repeatType: 'reverse' }}
          >
            <div className="w-16 h-16 bg-slate-100 rounded-full mb-4 mx-auto" />
            <div className="h-4 bg-slate-100 rounded w-3/4 mx-auto mb-2" />
            <div className="h-2 bg-slate-100 rounded w-1/2 mx-auto mb-6" />
            <div className="space-y-2">
              <div className="h-2 bg-slate-50 rounded w-full" />
              <div className="h-2 bg-slate-50 rounded w-full" />
              <div className="h-2 bg-slate-50 rounded w-5/6" />
              <div className="h-2 bg-slate-50 rounded w-full" />
            </div>
            <div className="mt-6 space-y-2">
              <div className="h-2 bg-slate-50 rounded w-full" />
              <div className="h-2 bg-slate-50 rounded w-full" />
            </div>
            {/* Scanning Line */}
            <motion.div
              className="absolute top-0 left-0 w-full h-1 bg-brand-500 shadow-[0_0_20px_rgba(59,130,246,0.5)]"
              animate={{ top: ['0%', '100%', '0%'] }}
              transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
            />
          </motion.div>

          {/* Job Description Card */}
          <motion.div
            className="absolute right-0 bottom-10 w-72 h-96 bg-slate-800 rounded-xl shadow-2xl p-6 z-0 border border-slate-700"
            initial={{ rotate: 5 }}
            animate={{ rotate: 2 }}
            transition={{ duration: 7, repeat: Infinity, repeatType: 'reverse' }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-indigo-500 rounded-lg flex items-center justify-center">
                <FileText className="text-white w-6 h-6" />
              </div>
              <div>
                <div className="h-3 bg-slate-600 rounded w-24 mb-1" />
                <div className="h-2 bg-slate-700 rounded w-16" />
              </div>
            </div>
            <div className="space-y-3">
              <div className="h-2 bg-slate-600 rounded w-full" />
              <div className="h-2 bg-slate-600 rounded w-11/12" />
              <div className="h-2 bg-slate-600 rounded w-full" />
              <div className="h-2 bg-slate-600 rounded w-3/4" />
            </div>
            <div className="mt-6">
              <div className="h-2 bg-slate-600 rounded w-1/3 mb-2" />
              <div className="flex flex-wrap gap-2">
                <span className="h-6 w-16 bg-slate-700 rounded-full" />
                <span className="h-6 w-20 bg-slate-700 rounded-full" />
                <span className="h-6 w-14 bg-slate-700 rounded-full" />
              </div>
            </div>
          </motion.div>

          {/* Connection Badge */}
          <motion.div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 bg-brand-500 rounded-full flex items-center justify-center shadow-xl z-20 border-4 border-slate-900"
            animate={{ scale: [1, 1.1, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          >
            <RefreshCw className="w-8 h-8 text-white animate-spin-slow" />
          </motion.div>

          {/* Floating Scores */}
          <motion.div
            className="absolute top-20 right-20 bg-green-500 text-white px-3 py-1 rounded-full text-sm font-bold shadow-lg flex items-center gap-1"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 }}
          >
            <CheckCircle className="w-3 h-3" /> {t.matchScore}
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}

export default Hero

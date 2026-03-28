import { Check, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import LanguageSwitcher from './LanguageSwitcher'

export interface WizardStep {
  id: number
  title: string
  subtitle: string
}

interface WizardLayoutProps {
  steps: WizardStep[]
  currentStep: number
  children: React.ReactNode
}

import { useTranslation } from 'react-i18next'

export default function WizardLayout({ steps, currentStep, children }: WizardLayoutProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Stepper Header */}
      <div className="bg-slate-900/80 backdrop-blur-lg border-b border-slate-800 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white group"
                title={t('wizard.home_tooltip')}
              >
                <Home className="w-5 h-5" />
                <span className="text-sm font-medium group-hover:text-white transition-colors">
                  {t('common.back_home')}
                </span>
              </button>
              <h1 className="text-lg font-semibold text-white">{t('wizard.page_title')}</h1>
            </div>
            <LanguageSwitcher />
          </div>
          <nav aria-label="Progress">
            <ol className="flex items-center justify-between relative z-0">
              {steps.map((step, index) => {
                const isCompleted = currentStep > step.id
                const isCurrent = currentStep === step.id

                return (
                  <li key={step.id} className="flex-1 relative">
                    <div className="flex items-center">
                      {/* Connector line - left side */}
                      {index > 0 && (
                        <div
                          className={`absolute left-0 right-1/2 top-5 h-0.5 -translate-y-1/2 ${
                            isCompleted || isCurrent ? 'bg-brand-500' : 'bg-slate-800'
                          }`}
                        />
                      )}

                      {/* Connector line - right side */}
                      {index < steps.length - 1 && (
                        <div
                          className={`absolute left-1/2 right-0 top-5 h-0.5 -translate-y-1/2 ${
                            isCompleted ? 'bg-brand-500' : 'bg-slate-800'
                          }`}
                        />
                      )}

                      {/* Step indicator */}
                      <div className="relative flex flex-col items-center w-full">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold z-10 transition-all duration-300 ${
                            isCompleted
                              ? 'bg-brand-600 text-white shadow-lg shadow-brand-500/25'
                              : isCurrent
                                ? 'bg-brand-500 text-white ring-4 ring-brand-500/20 shadow-lg shadow-brand-500/40 scale-110'
                                : 'bg-slate-800 text-slate-500 border border-slate-700'
                          }`}
                        >
                          {isCompleted ? <Check className="w-5 h-5" /> : step.id}
                        </div>
                        <div className="mt-3 text-center">
                          <div
                            className={`text-sm font-medium transition-colors ${
                              isCurrent
                                ? 'text-brand-400'
                                : isCompleted
                                  ? 'text-white'
                                  : 'text-slate-500'
                            }`}
                          >
                            {step.title}
                          </div>
                          <div
                            className={`text-xs mt-0.5 hidden sm:block transition-colors ${isCurrent ? 'text-brand-300/70' : 'text-slate-600'}`}
                          >
                            {step.subtitle}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                )
              })}
            </ol>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 py-8 relative">
        {/* Background glow for content area */}
        <div className="absolute top-20 left-1/2 -translate-x-1/2 w-full h-96 bg-brand-500/5 blur-[100px] rounded-full pointer-events-none -z-10" />
        {children}
      </div>
    </div>
  )
}

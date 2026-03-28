import { useNavigate } from 'react-router-dom'
import { FileText, Sparkles, ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import LanguageSwitcher from '@/components/LanguageSwitcher'
// FEEDBACK FEATURE - remove these imports to disable
import { FeedbackBanner, FeedbackModal, useFeedback } from '@/features/feedback'

export default function HomePage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  // FEEDBACK FEATURE - remove this hook to disable
  const feedback = useFeedback()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12 relative">
          <div className="absolute right-0 top-0">
            <LanguageSwitcher />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">{t('header.title')}</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">{t('home.subtitle')}</p>
        </div>

        {/* FEEDBACK FEATURE - remove this banner to disable */}
        {feedback.isEnabled && (
          <div className="mb-6">
            <FeedbackBanner onClick={feedback.showFeedback} />
          </div>
        )}

        {/* Mode Cards */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Wizard Mode */}
          <button
            onClick={() => navigate('/wizard')}
            className="group bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-left border-2 border-transparent hover:border-blue-500"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-500 transition-colors">
                <FileText className="w-7 h-7 text-blue-600 group-hover:text-white transition-colors" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{t('home.title')}</h2>
                <span className="text-sm text-blue-600 font-medium">
                  {t('wizard.steps.improvement')}
                </span>
              </div>
            </div>

            <p className="text-gray-600 mb-6">{t('home.subtitle')}</p>

            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs font-medium">
                  1
                </span>
                {t('wizard.steps.resume')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs font-medium">
                  2
                </span>
                {t('wizard.steps.vacancy')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs font-medium">
                  3
                </span>
                {t('wizard.steps.analysis')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs font-medium">
                  4
                </span>
                {t('wizard.steps.improvement')}
              </div>
            </div>

            <div className="flex items-center text-blue-600 font-medium group-hover:gap-2 transition-all">
              {t('home.start_button')} <ArrowRight className="w-4 h-4 ml-1" />
            </div>
          </button>

          {/* Ideal Resume Mode */}
          <button
            onClick={() => navigate('/ideal-resume')}
            className="group bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 text-left border-2 border-transparent hover:border-purple-500"
          >
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 bg-purple-100 rounded-xl flex items-center justify-center group-hover:bg-purple-500 transition-colors">
                <Sparkles className="w-7 h-7 text-purple-600 group-hover:text-white transition-colors" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{t('home.ideal_title')}</h2>
                <span className="text-sm text-purple-600 font-medium">
                  {t('home.ideal_subtitle')}
                </span>
              </div>
            </div>

            <p className="text-gray-600 mb-6">{t('home.ideal_description')}</p>

            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-medium">
                  1
                </span>
                {t('home.steps_data')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-medium">
                  2
                </span>
                {t('home.steps_vacancy')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-medium">
                  3
                </span>
                {t('home.steps_generation')}
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-medium">
                  4
                </span>
                {t('home.steps_editing')}
              </div>
            </div>

            <div className="flex items-center text-purple-600 font-medium group-hover:gap-2 transition-all">
              {t('home.start_button')} <ArrowRight className="w-4 h-4 ml-1" />
            </div>
          </button>
        </div>

        {/* Footer */}
        <p className="text-center text-gray-500 text-sm mt-8">{t('common.footer')}</p>
      </div>

      {/* FEEDBACK FEATURE - remove this modal to disable */}
      {feedback.isEnabled && (
        <FeedbackModal isOpen={feedback.isOpen} onClose={feedback.closeFeedback} source="manual" />
      )}
    </div>
  )
}

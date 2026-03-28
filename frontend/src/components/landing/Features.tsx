import React from 'react'
import { Target, Wand2, FileCheck, ShieldCheck, Zap, BarChart3 } from 'lucide-react'
import { Language } from './types'

interface FeaturesProps {
  lang: Language
}

const Features: React.FC<FeaturesProps> = ({ lang }) => {
  const content = {
    en: {
      subtitle: 'Features',
      title: 'Everything you need to beat the ATS',
      description:
        'EdtonAI combines advanced LLMs with recruiter-approved templates to give you an unfair advantage.',
      items: [
        {
          title: 'Smart Scoring',
          description:
            'Get an instant 0-100% match score against any vacancy. Know exactly where you stand before you apply.',
        },
        {
          title: 'AI Adaptation',
          description:
            'Our AI automatically rewrites your weak bullet points to perfectly match the keywords in the job description.',
        },
        {
          title: 'ATS-Proof Format',
          description:
            'Download perfectly formatted PDF/DOCX files that are guaranteed to pass Applicant Tracking Systems.',
        },
        {
          title: 'Keyword Analysis',
          description:
            'Identify missing keywords that are hurting your chances and seamlessly integrate them into your profile.',
        },
        {
          title: 'Instant Generation',
          description:
            'Paste a LinkedIn job URL and get a tailored resume generated in seconds, not hours.',
        },
        {
          title: 'Secure & Private',
          description:
            'Your data is encrypted and never shared. We prioritize your privacy above all else.',
        },
      ],
    },
    ru: {
      subtitle: 'Возможности',
      title: 'Всё необходимое, чтобы обойти ATS',
      description:
        'EdtonAI объединяет передовые LLM с проверенными шаблонами, чтобы дать вам несправедливое преимущество.',
      items: [
        {
          title: 'Умная оценка',
          description:
            'Получите мгновенную оценку соответствия вакансии (0-100%). Знайте свои шансы до отправки резюме.',
        },
        {
          title: 'ИИ Адаптация',
          description:
            'Наш ИИ автоматически переписывает слабые места, идеально подбирая ключевые слова из описания вакансии.',
        },
        {
          title: 'Формат для ATS',
          description:
            'Скачивайте идеально отформатированные файлы PDF/DOCX, гарантированно проходящие системы отслеживания кандидатов.',
        },
        {
          title: 'Анализ ключевых слов',
          description:
            'Выявляйте недостающие ключевые слова, снижающие ваши шансы, и легко интегрируйте их в профиль.',
        },
        {
          title: 'Мгновенная генерация',
          description:
            'Вставьте ссылку на вакансию LinkedIn и получите адаптированное резюме за секунды, а не часы.',
        },
        {
          title: 'Безопасность и приватность',
          description:
            'Ваши данные зашифрованы и никогда не передаются третьим лицам. Конфиденциальность — наш приоритет.',
        },
      ],
    },
  }

  const t = content[lang]
  const icons = [Target, Wand2, FileCheck, BarChart3, Zap, ShieldCheck]

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-900 relative">
      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent" />

      <div className="container mx-auto">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-brand-400 font-semibold tracking-wide uppercase text-sm mb-3">
            {t.subtitle}
          </h2>
          <h3 className="text-3xl md:text-4xl font-bold text-white mb-6">{t.title}</h3>
          <p className="text-slate-400 text-lg">{t.description}</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {t.items.map((feature, index) => {
            const Icon = icons[index]
            return (
              <div
                key={index}
                className="glass-card p-8 rounded-2xl hover:bg-white/10 transition-colors group cursor-default border border-slate-700 hover:border-slate-600 bg-slate-800/50"
              >
                <div className="w-12 h-12 bg-brand-900/50 rounded-lg flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 border border-brand-500/20">
                  <Icon className="w-6 h-6 text-brand-400" />
                </div>
                <h4 className="text-xl font-semibold text-white mb-3">{feature.title}</h4>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default Features

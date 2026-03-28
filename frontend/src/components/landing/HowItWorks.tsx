import React from 'react'
import { Upload, Cpu, MousePointerClick, Download } from 'lucide-react'
import { Language } from './types'

interface HowItWorksProps {
  lang: Language
}

const HowItWorks: React.FC<HowItWorksProps> = ({ lang }) => {
  const content = {
    en: {
      title: 'How It Works',
      description:
        "Optimizing your resume shouldn't be rocket science. We've simplified the process into four easy steps.",
      steps: [
        {
          title: 'Upload & Paste',
          description:
            'Upload your current resume and paste the job description you want to apply for.',
        },
        {
          title: 'AI Analysis',
          description:
            'Our engine scans both documents to find gaps, missing keywords, and formatting issues.',
        },
        {
          title: 'Select Improvements',
          description:
            'Review AI-suggested rewrites and accept the ones that best describe your experience.',
        },
        {
          title: 'Download & Apply',
          description:
            'Get your perfectly tailored resume in PDF or Word format and apply with confidence.',
        },
      ],
    },
    ru: {
      title: 'Как это работает',
      description:
        'Оптимизация резюме не должна быть сложной. Мы упростили процесс до четырех простых шагов.',
      steps: [
        {
          title: 'Загрузи и Вставь',
          description:
            'Загрузите текущее резюме и вставьте описание вакансии, на которую хотите откликнуться.',
        },
        {
          title: 'Анализ ИИ',
          description:
            'Наш движок сканирует оба документа, чтобы найти пробелы, недостающие ключевые слова и ошибки форматирования.',
        },
        {
          title: 'Выбери улучшения',
          description:
            'Просмотрите предложенные ИИ варианты и выберите те, которые лучше всего описывают ваш опыт.',
        },
        {
          title: 'Скачай и Отправь',
          description:
            'Получите идеально адаптированное резюме в формате PDF или Word и отправляйте с уверенностью.',
        },
      ],
    },
  }

  const t = content[lang]
  const icons = [Upload, Cpu, MousePointerClick, Download]

  return (
    <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-900 relative overflow-hidden">
      {/* Decorative gradient */}
      <div className="absolute bottom-0 right-0 w-1/3 h-1/3 bg-brand-600/10 blur-[100px] rounded-full pointer-events-none" />

      <div className="container mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">{t.title}</h2>
          <p className="text-slate-400 max-w-2xl mx-auto">{t.description}</p>
        </div>

        <div className="grid md:grid-cols-4 gap-8 relative">
          {/* Connector Line (Desktop) */}
          <div className="hidden md:block absolute top-12 left-[10%] right-[10%] h-0.5 bg-slate-800 z-0"></div>

          {t.steps.map((step, index) => {
            const Icon = icons[index]
            return (
              <div key={index} className="relative z-10 flex flex-col items-center text-center">
                <div className="w-24 h-24 bg-slate-800 rounded-full border-4 border-slate-900 flex items-center justify-center mb-6 shadow-xl relative group">
                  <Icon className="w-8 h-8 text-brand-400 group-hover:scale-110 transition-transform" />
                  <div className="absolute -top-2 -right-2 w-8 h-8 bg-brand-600 rounded-full flex items-center justify-center text-white font-bold text-sm border-4 border-slate-900">
                    {index + 1}
                  </div>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{step.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default HowItWorks

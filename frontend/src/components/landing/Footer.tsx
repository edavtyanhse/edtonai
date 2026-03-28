import React from 'react'
import { Twitter, Linkedin, Github } from 'lucide-react'
import { Language } from './types'

interface FooterProps {
  lang: Language
}

const Footer: React.FC<FooterProps> = ({ lang }) => {
  const content = {
    en: {
      description:
        'Empowering job seekers with AI technology to break through ATS barriers and land their dream jobs.',
      product: 'Product',
      company: 'Company',
      links: {
        scorer: 'Resume Scorer',
        coverLetter: 'Cover Letter Gen',
        linkedin: 'LinkedIn Optimization',
        pricing: 'Pricing',
        about: 'About Us',
        blog: 'Blog',
        privacy: 'Privacy Policy',
        terms: 'Terms of Service',
      },
    },
    ru: {
      description:
        'Помогаем соискателям использовать технологии ИИ, чтобы преодолеть барьеры ATS и получить работу мечты.',
      product: 'Продукт',
      company: 'Компания',
      links: {
        scorer: 'Оценка резюме',
        coverLetter: 'Генератор писем',
        linkedin: 'Оптимизация LinkedIn',
        pricing: 'Цены',
        about: 'О нас',
        blog: 'Блог',
        privacy: 'Конфиденциальность',
        terms: 'Условия использования',
      },
    },
  }

  const t = content[lang]

  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 py-12 px-4">
      <div className="container mx-auto grid md:grid-cols-4 gap-8">
        <div className="col-span-1 md:col-span-2">
          <div className="flex items-center gap-2 text-white font-bold text-xl mb-4">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              E
            </div>
            EdtonAI
          </div>
          <p className="text-sm max-w-sm">{t.description}</p>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">{t.product}</h4>
          <ul className="space-y-2 text-sm">
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.scorer}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.coverLetter}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.linkedin}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.pricing}
              </a>
            </li>
          </ul>
        </div>

        <div>
          <h4 className="text-white font-semibold mb-4">{t.company}</h4>
          <ul className="space-y-2 text-sm">
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.about}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.blog}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.privacy}
              </a>
            </li>
            <li>
              <a href="#" className="hover:text-brand-400 transition-colors">
                {t.links.terms}
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="container mx-auto mt-12 pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="text-xs">&copy; {new Date().getFullYear()} EdtonAI. All rights reserved.</p>
        <div className="flex gap-4">
          <a href="#" className="hover:text-white transition-colors">
            <Twitter className="w-5 h-5" />
          </a>
          <a href="#" className="hover:text-white transition-colors">
            <Linkedin className="w-5 h-5" />
          </a>
          <a href="#" className="hover:text-white transition-colors">
            <Github className="w-5 h-5" />
          </a>
        </div>
      </div>
    </footer>
  )
}

export default Footer

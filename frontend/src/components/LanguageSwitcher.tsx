import { useTranslation } from 'react-i18next'
import { Button } from '@/components'

export default function LanguageSwitcher() {
  const { i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ru' ? 'en' : 'ru'
    i18n.changeLanguage(newLang)
  }

  return (
    <Button variant="ghost" size="sm" onClick={toggleLanguage} className="w-12">
      {/* Use simple text or icon - keep it minimal */}
      <span className="font-bold text-xs">{i18n.language === 'ru' ? 'RU' : 'EN'}</span>
    </Button>
  )
}

import { useState, useEffect } from 'react'
import { Copy, X, Check, Briefcase, User, Award } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Button from './Button'
import { toast } from './toastUtils'
import type { ParsedResume } from '@/api'

interface Props {
    data: ParsedResume
    onClose: () => void
}

type Tab = 'experience' | 'skills' | 'about'

export default function HeadHunterPreview({ data, onClose }: Props) {
    const { t } = useTranslation()
    const [activeTab, setActiveTab] = useState<Tab>('experience')
    const [copiedId, setCopiedId] = useState<string | null>(null)

    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', handleEsc)
        return () => window.removeEventListener('keydown', handleEsc)
    }, [onClose])

    const handleCopy = async (text: string, id: string) => {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(text)
            } else {
                // Fallback using document.execCommand
                const textArea = document.createElement("textarea")
                textArea.value = text
                textArea.style.position = "fixed"
                textArea.style.left = "-9999px"
                textArea.style.top = "0"
                document.body.appendChild(textArea)
                textArea.focus()
                textArea.select()
                document.execCommand('copy')
                document.body.removeChild(textArea)
            }
            setCopiedId(id)
            setTimeout(() => setCopiedId(null), 2000)
        } catch (err) {
            console.error('Failed to copy text: ', err)
            toast('error', t('common.error_copy', 'Ошибка при копировании'))
        }
    }

    const { work_experience, skills, summary } = data

    const getFullExportText = () => {
        const sections = []

        if (work_experience?.length) {
            sections.push('--- ОПЫТ РАБОТЫ ---')
            work_experience.forEach(exp => {
                sections.push(`${exp.company} | ${exp.title}`)
                sections.push(`${exp.start_date} - ${exp.end_date || 'н.в.'}`)
                const lines = []
                if (exp.responsibilities) lines.push(...exp.responsibilities)
                if (exp.achievements) lines.push(...exp.achievements)
                sections.push(lines.map(l => `• ${l}`).join('\n'))
                sections.push('')
            })
        }

        if (skills?.length) {
            sections.push('--- КЛЮЧЕВЫЕ НАВЫКИ ---')
            sections.push(skills.map(s => s.name).join(', '))
            sections.push('')
        }

        if (summary) {
            sections.push('--- О СЕБЕ ---')
            sections.push(summary)
        }

        return sections.join('\n')
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="hh-preview-title"
        >
            <div className="bg-slate-900 border border-slate-700 w-full max-w-4xl h-[85vh] rounded-xl shadow-2xl flex flex-col overflow-hidden text-slate-100">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-800/50">
                    <div>
                        <div className="flex items-center gap-2">
                            <h2 id="hh-preview-title" className="text-xl font-bold text-white">
                                {t('wizard.step4.hh_export', 'Экспорт для hh.ru')}
                            </h2>
                            <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] font-bold uppercase tracking-wider rounded border border-blue-500/30">Beta</span>
                        </div>
                        <p className="text-sm text-slate-400">{t('wizard.step4.hh_export_desc', 'Скопируйте блоки текста в форму резюме на HeadHunter')}</p>
                    </div>
                    <Button
                        variant="ghost"
                        onClick={onClose}
                        className="text-slate-400 hover:text-white hover:bg-slate-700"
                        aria-label={t('common.close', 'Закрыть')}
                    >
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-slate-700 bg-slate-900/50">
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'experience'
                            ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/5'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                        onClick={() => setActiveTab('experience')}
                        aria-selected={activeTab === 'experience'}
                        role="tab"
                    >
                        <Briefcase className="w-4 h-4" />
                        <span className="hidden sm:inline">{t('wizard.steps.experience', 'Опыт работы')}</span>
                        <span className="sm:hidden">{t('wizard.step3.score_experience', 'Опыт')}</span>
                    </button>
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'skills'
                            ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/5'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                        onClick={() => setActiveTab('skills')}
                        aria-selected={activeTab === 'skills'}
                        role="tab"
                    >
                        <Award className="w-4 h-4" />
                        <span className="hidden sm:inline">{t('wizard.step3.required_skills', 'Ключевые навыки')}</span>
                        <span className="sm:hidden">{t('wizard.step3.score_skills', 'Навыки')}</span>
                    </button>
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${activeTab === 'about'
                            ? 'text-blue-400 border-b-2 border-blue-500 bg-blue-500/5'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                        onClick={() => setActiveTab('about')}
                        aria-selected={activeTab === 'about'}
                        role="tab"
                    >
                        <User className="w-4 h-4" />
                        <span className="hidden sm:inline">{t('wizard.step4.about', 'О себе')}</span>
                        <span className="sm:hidden">{t('wizard.step4.about', 'О себе')}</span>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-slate-900 custom-scrollbar">

                    {/* EXPERIENCE TAB */}
                    {activeTab === 'experience' && (
                        <div className="space-y-6">
                            {!work_experience?.length && (
                                <div className="text-center text-slate-500 py-10">{t('wizard.step3.no_data', 'Нет данных')}</div>
                            )}
                            {work_experience?.map((exp, i) => {
                                // Formatting for HH: Bullet points
                                const lines = []
                                if (exp.responsibilities) lines.push(...exp.responsibilities)
                                if (exp.achievements) {
                                    if (exp.responsibilities?.length) lines.push('') // spacer
                                    lines.push('Достижения:')
                                    lines.push(...exp.achievements)
                                }
                                const textToCopy = lines.map(l => l.startsWith('•') || l.endsWith(':') || l === '' ? l : `• ${l}`).join('\n')
                                const id = `exp-${i}`

                                return (
                                    <div key={i} className="bg-slate-800/50 rounded-lg border border-slate-700 shadow-sm p-4 hover:border-slate-600 transition-colors group">
                                        <div className="flex flex-col sm:flex-row justify-between items-start gap-3 mb-4">
                                            <div className="flex-1">
                                                <h3 className="font-bold text-white text-lg">{exp.company}</h3>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-blue-400 font-medium">{exp.title}</span>
                                                    <span className="text-slate-600">•</span>
                                                    <span className="text-slate-400 text-xs">
                                                        {exp.start_date} — {exp.end_date || 'н.в'}
                                                    </span>
                                                </div>
                                            </div>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleCopy(textToCopy, id)}
                                                className={`transition-all ${copiedId === id
                                                    ? "text-green-400 border-green-500/50 bg-green-500/10"
                                                    : "text-slate-300 border-slate-600 hover:bg-slate-700"}`}
                                            >
                                                {copiedId === id ? <Check className="w-3 h-3 mr-1.5" /> : <Copy className="w-3 h-3 mr-1.5" />}
                                                {copiedId === id ? t('wizard.step4.copied', 'Скопировано') : t('wizard.step4.copy', 'Копировать')}
                                            </Button>
                                        </div>
                                        <div className="bg-slate-900/50 p-3 rounded text-sm text-slate-300 whitespace-pre-wrap border border-slate-700/50 font-mono leading-relaxed">
                                            {textToCopy}
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    )}

                    {/* SKILLS TAB */}
                    {activeTab === 'skills' && (
                        <div className="space-y-6">
                            <div className="bg-slate-800/50 rounded-lg border border-slate-700 shadow-sm p-4">
                                <div className="flex justify-between items-center mb-6">
                                    <h3 className="font-bold text-white uppercase tracking-wider text-xs">{t('wizard.step3.required_skills', 'Ключевые навыки')}</h3>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleCopy(skills?.map(s => s.name).join(', ') || '', 'skills-all')}
                                        className={copiedId === 'skills-all' ? "text-green-400 border-green-500/50 bg-green-500/10" : "border-slate-600"}
                                    >
                                        {copiedId === 'skills-all' ? <Check className="w-3 h-3 mr-1.5" /> : <Copy className="w-3 h-3 mr-1.5" />}
                                        {t('wizard.step4.hh_copy_list', 'Копировать списком')}
                                    </Button>
                                </div>

                                <div className="flex flex-wrap gap-2">
                                    {skills?.map((skill, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleCopy(skill.name, `skill-${i}`)}
                                            title={t('wizard.step4.copy', 'Копировать')}
                                            className={`px-3 py-1 rounded-md text-sm border transition-all flex items-center gap-2 group/skill ${copiedId === `skill-${i}`
                                                ? "bg-green-500/20 text-green-300 border-green-500/50"
                                                : "bg-blue-500/10 text-blue-300 border-blue-500/20 hover:border-blue-400/50 hover:bg-blue-500/20"
                                                }`}
                                        >
                                            {skill.name}
                                            {copiedId === `skill-${i}`
                                                ? <Check className="w-3 h-3 text-green-400" />
                                                : <Copy className="w-3 h-3 opacity-0 group-hover/skill:opacity-50 transition-opacity" />
                                            }
                                        </button>
                                    ))}
                                    {!skills?.length && <p className="text-slate-500">{t('wizard.step3.no_data', 'Нет данных')}</p>}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ABOUT TAB */}
                    {activeTab === 'about' && (
                        <div className="space-y-6">
                            <div className="bg-slate-800/50 rounded-lg border border-slate-700 shadow-sm p-4">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-bold text-white uppercase tracking-wider text-xs">{t('wizard.step4.about', 'О себе')}</h3>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleCopy(summary || '', 'summary')}
                                        className={copiedId === 'summary' ? "text-green-400 border-green-500/50 bg-green-500/10" : "border-slate-600"}
                                    >
                                        {copiedId === 'summary' ? <Check className="w-3 h-3 mr-1.5" /> : <Copy className="w-3 h-3 mr-1.5" />}
                                        {t('wizard.step4.copy', 'Копировать')}
                                    </Button>
                                </div>
                                <div className="bg-slate-900/50 p-4 rounded text-sm text-slate-300 whitespace-pre-wrap border border-slate-700/50 leading-relaxed italic">
                                    {summary || t('wizard.step3.no_data', 'Нет данных')}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-slate-700 bg-slate-800/50 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <Button
                        variant="outline"
                        className="w-full sm:w-auto text-slate-300 border-slate-600 hover:bg-slate-700 order-2 sm:order-1"
                        onClick={() => handleCopy(getFullExportText(), 'full-export')}
                    >
                        {copiedId === 'full-export' ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
                        {t('wizard.step4.hh_copy_all', 'Копировать всё сразу')}
                    </Button>
                    <div className="flex gap-3 w-full sm:w-auto order-1 sm:order-2">
                        <Button onClick={onClose} className="flex-1 sm:flex-none">
                            {t('common.close', 'Закрыть')}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}

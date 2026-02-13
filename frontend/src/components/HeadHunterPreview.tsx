
import { useState } from 'react'
import { Copy, X, Check, Briefcase, User, Award } from 'lucide-react'
import { Button } from '@/components'
import type { ParsedResume } from '@/api'

interface Props {
    data: ParsedResume
    onClose: () => void
}

type Tab = 'experience' | 'skills' | 'about'

export default function HeadHunterPreview({ data, onClose }: Props) {
    const [activeTab, setActiveTab] = useState<Tab>('experience')
    const [copiedId, setCopiedId] = useState<string | null>(null)

    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text)
        setCopiedId(id)
        setTimeout(() => setCopiedId(null), 2000)
    }

    const { work_experience, skills, summary } = data

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="bg-white w-full max-w-4xl h-[85vh] rounded-xl shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b bg-gray-50">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Экспорт для hh.ru</h2>
                        <p className="text-sm text-gray-500">Копируйте готовые блоки текста в форму резюме на HeadHunter</p>
                    </div>
                    <Button variant="ghost" onClick={onClose}>
                        <X className="w-5 h-5" />
                    </Button>
                </div>

                {/* Tabs */}
                <div className="flex border-b">
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${activeTab === 'experience'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-600 hover:bg-gray-50'
                            }`}
                        onClick={() => setActiveTab('experience')}
                    >
                        <Briefcase className="w-4 h-4" />
                        Опыт работы
                    </button>
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${activeTab === 'skills'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-600 hover:bg-gray-50'
                            }`}
                        onClick={() => setActiveTab('skills')}
                    >
                        <Award className="w-4 h-4" />
                        Навыки
                    </button>
                    <button
                        className={`flex-1 px-4 py-3 text-sm font-medium flex items-center justify-center gap-2 ${activeTab === 'about'
                                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                                : 'text-gray-600 hover:bg-gray-50'
                            }`}
                        onClick={() => setActiveTab('about')}
                    >
                        <User className="w-4 h-4" />
                        О себе
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-gray-50/50">

                    {/* EXPERIENCE TAB */}
                    {activeTab === 'experience' && (
                        <div className="space-y-6">
                            {!work_experience?.length && (
                                <div className="text-center text-gray-500 py-10">Опыт работы не указан</div>
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
                                    <div key={i} className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <h3 className="font-bold text-gray-900">{exp.company}</h3>
                                                <p className="text-sm text-gray-600">{exp.title}</p>
                                                <p className="text-xs text-gray-400 mt-1">
                                                    {exp.start_date} — {exp.end_date || 'по настоящее время'}
                                                </p>
                                            </div>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleCopy(textToCopy, id)}
                                                className={copiedId === id ? "text-green-600 border-green-200 bg-green-50" : ""}
                                            >
                                                {copiedId === id ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                                                {copiedId === id ? 'Скопировано' : 'Копировать'}
                                            </Button>
                                        </div>
                                        <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap border font-mono">
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
                            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="font-bold text-gray-900">Ключевые навыки</h3>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleCopy(skills?.map(s => s.name).join(', ') || '', 'skills-all')}
                                    >
                                        {copiedId === 'skills-all' ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                                        Копировать списком
                                    </Button>
                                </div>

                                <div className="flex flex-wrap gap-2">
                                    {skills?.map((skill, i) => (
                                        <span key={i} className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-100">
                                            {skill.name}
                                        </span>
                                    ))}
                                    {!skills?.length && <p className="text-gray-500">Навыки не найдены</p>}
                                </div>
                            </div>

                            {/* Tech Stack for separate field if needed, but HH uses tags mostly */}
                        </div>
                    )}

                    {/* ABOUT TAB */}
                    {activeTab === 'about' && (
                        <div className="space-y-6">
                            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
                                <div className="flex justify-between items-center mb-3">
                                    <h3 className="font-bold text-gray-900">О себе</h3>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={() => handleCopy(summary || '', 'summary')}
                                    >
                                        {copiedId === 'summary' ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
                                        Копировать
                                    </Button>
                                </div>
                                <div className="bg-gray-50 p-3 rounded text-sm text-gray-700 whitespace-pre-wrap border">
                                    {summary || 'Секция "О себе" пуста'}
                                </div>
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer */}
                <div className="p-4 border-t bg-white flex justify-end">
                    <Button onClick={onClose}>Закрыть</Button>
                </div>
            </div>
        </div>
    )
}

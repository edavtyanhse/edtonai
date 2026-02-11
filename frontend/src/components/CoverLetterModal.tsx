import { X, Copy, Download, Loader2 } from 'lucide-react'
import { useState } from 'react'
import Button from './Button'

interface CoverLetterModalProps {
  isOpen: boolean
  onClose: () => void
  coverLetter: string
  structure?: {
    opening: string
    body: string
    closing: string
  }
  keyPoints?: string[]
  alignmentNotes?: string[]
  isLoading?: boolean
}

export function CoverLetterModal({
  isOpen,
  onClose,
  coverLetter,
  structure,
  keyPoints,
  alignmentNotes,
  isLoading = false,
}: CoverLetterModalProps) {
  const [copied, setCopied] = useState(false)

  if (!isOpen) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(coverLetter)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([coverLetter], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cover-letter-${new Date().toISOString().split('T')[0]}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[90vh] bg-white dark:bg-gray-800 rounded-lg shadow-xl flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Сопроводительное письмо
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            aria-label="Закрыть"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
              <span className="ml-3 text-gray-600 dark:text-gray-400">
                Генерируем письмо...
              </span>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Main Text */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
                <pre className="whitespace-pre-wrap font-sans text-gray-800 dark:text-gray-200 leading-relaxed">
                  {coverLetter}
                </pre>
              </div>

              {/* Structure Breakdown */}
              {structure && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Структура письма
                  </h3>
                  <div className="space-y-3">
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                      <h4 className="font-medium text-blue-900 dark:text-blue-200 mb-2">
                        Вступление
                      </h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {structure.opening}
                      </p>
                    </div>
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                      <h4 className="font-medium text-green-900 dark:text-green-200 mb-2">
                        Основная часть
                      </h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {structure.body}
                      </p>
                    </div>
                    <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                      <h4 className="font-medium text-purple-900 dark:text-purple-200 mb-2">
                        Заключение
                      </h4>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {structure.closing}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Key Points Used */}
              {keyPoints && keyPoints.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Использованные факты из резюме
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                    {keyPoints.map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Alignment Notes */}
              {alignmentNotes && alignmentNotes.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Соответствие вакансии
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                    {alignmentNotes.map((note, idx) => (
                      <li key={idx}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {!isLoading && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
            <Button variant="outline" onClick={handleDownload} icon={<Download />}>
              Скачать
            </Button>
            <Button onClick={handleCopy} icon={<Copy />}>
              {copied ? 'Скопировано!' : 'Копировать'}
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

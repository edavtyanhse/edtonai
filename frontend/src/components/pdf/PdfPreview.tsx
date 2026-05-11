import { useEffect, useMemo } from 'react'
import { usePDF } from '@react-pdf/renderer'
import { X, Download, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components'
import HarvardTemplate from './HarvardTemplate'
import type { ParsedResume } from '@/api'

interface PdfPreviewProps {
  data: ParsedResume
  onClose: () => void
}

export default function PdfPreview({ data, onClose }: PdfPreviewProps) {
  const document = useMemo(() => <HarvardTemplate data={data} />, [data])
  const [instance, updateInstance] = usePDF({ document })

  // Re-render whenever the resume data changes
  useEffect(() => {
    updateInstance(document)
  }, [document, updateInstance])

  const downloadHref = instance.url ?? undefined
  const isReady = !instance.loading && !instance.error && !!instance.url

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white w-full max-w-5xl h-[90vh] rounded-xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold text-gray-900">Preview PDF</h2>
          <div className="flex gap-2">
            <a
              href={downloadHref}
              download="Result_Resume.pdf"
              onClick={(e) => {
                if (!isReady) e.preventDefault()
              }}
              className={!isReady ? 'pointer-events-none' : ''}
            >
              <Button disabled={!isReady}>
                <Download className="w-4 h-4 mr-2" />
                {instance.loading ? 'Generating...' : 'Download PDF'}
              </Button>
            </a>
            <Button variant="ghost" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Viewer */}
        <div className="flex-1 bg-gray-100 p-4 overflow-hidden flex items-center justify-center">
          {instance.loading && (
            <div className="flex flex-col items-center text-gray-600 gap-2">
              <Loader2 className="w-8 h-8 animate-spin" />
              <span>Building PDF...</span>
            </div>
          )}
          {instance.error && (
            <div className="flex flex-col items-center text-red-600 gap-2 max-w-md text-center px-4">
              <AlertCircle className="w-8 h-8" />
              <span className="font-medium">PDF render failed</span>
              <span className="text-xs text-gray-600 break-all">{String(instance.error)}</span>
            </div>
          )}
          {isReady && (
            <iframe
              src={instance.url ?? ''}
              title="Resume PDF preview"
              className="w-full h-full rounded shadow-sm bg-white"
            />
          )}
        </div>
      </div>
    </div>
  )
}

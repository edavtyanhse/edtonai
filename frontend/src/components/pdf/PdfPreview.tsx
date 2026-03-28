import { PDFViewer, PDFDownloadLink } from '@react-pdf/renderer'
import { X, Download } from 'lucide-react'
import { Button } from '@/components'
import HarvardTemplate from './HarvardTemplate'
import type { ParsedResume } from '@/api'

interface PdfPreviewProps {
  data: ParsedResume
  onClose: () => void
}

export default function PdfPreview({ data, onClose }: PdfPreviewProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white w-full max-w-5xl h-[90vh] rounded-xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-bold text-gray-900">Preview PDF</h2>
          <div className="flex gap-2">
            <PDFDownloadLink
              document={<HarvardTemplate data={data} />}
              fileName={`Result_Resume.pdf`}
            >
              {({ loading }) => (
                <Button disabled={loading}>
                  <Download className="w-4 h-4 mr-2" />
                  {loading ? 'Generating...' : 'Download PDF'}
                </Button>
              )}
            </PDFDownloadLink>
            <Button variant="ghost" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Viewer */}
        <div className="flex-1 bg-gray-100 p-4 overflow-hidden">
          <PDFViewer width="100%" height="100%" className="rounded shadow-sm">
            <HarvardTemplate data={data} />
          </PDFViewer>
        </div>
      </div>
    </div>
  )
}

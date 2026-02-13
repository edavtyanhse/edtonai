import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Trash2, Eye, RotateCcw, FileText, Sparkles, Calendar, ArrowLeft } from 'lucide-react'
import { Button, ConfirmDialog } from '@/components'
import { getVersions, getVersion, deleteVersion, type VersionItem, type VersionDetail } from '@/api'

interface RestoreVersionState {
  restoreVersion: {
    resumeText: string
    vacancyText: string
    resultText: string
  }
}

export default function History() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()

  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(
    searchParams.get('view')
  )
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Fetch versions list
  const {
    data: versionsData,
    isLoading: isLoadingList,
    error: listError,
  } = useQuery({
    queryKey: ['versions'],
    queryFn: () => getVersions(50, 0),
  })

  // Fetch selected version detail
  const {
    data: selectedVersion,
    isLoading: isLoadingDetail,
  } = useQuery({
    queryKey: ['version', selectedVersionId],
    queryFn: () => getVersion(selectedVersionId!),
    enabled: !!selectedVersionId,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteVersion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['versions'] })
      if (selectedVersionId === deleteConfirm) {
        setSelectedVersionId(null)
      }
      setDeleteConfirm(null)
    },
  })

  const handleView = (id: string) => {
    setSelectedVersionId(id)
  }



  const handleRestore = (version: VersionDetail) => {
    navigate('/', {
      state: {
        restoreVersion: {
          resumeText: version.resume_text || '',
          vacancyText: version.vacancy_text,
          resultText: version.result_text,
        },
      } satisfies RestoreVersionState,
    })
  }

  const handleDelete = (id: string) => {
    setDeleteConfirm(id)
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const truncate = (text: string, length: number) => {
    if (!text) return ''
    return text.length > length ? text.slice(0, length) + '...' : text
  }

  const versions = versionsData?.items || []

  return (
    <div className="space-y-6">
      {/* Header with back button */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/')} className="text-slate-400 hover:text-white">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <h1 className="text-2xl font-bold text-white">Version History</h1>
      </div>

      {listError && (
        <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300 text-sm">
          Failed to load versions: {(listError as Error).message}
        </div>
      )}

      {isLoadingList ? (
        <div className="text-center py-12 text-slate-400">Loading...</div>
      ) : versions.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 mb-4">No saved versions yet</p>
          <Button onClick={() => navigate('/')}>
            Create your first version
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-6">
          {/* Version list */}
          <div className="col-span-1 space-y-2">
            {versions.map((version: VersionItem) => (
              <VersionCard
                key={version.id}
                version={version}
                isSelected={selectedVersionId === version.id}
                onView={() => handleView(version.id)}
                // onCompare={() => handleCompare(version.id)}
                onDelete={() => handleDelete(version.id)}
                formatDate={formatDate}
                truncate={truncate}
              />
            ))}
          </div>

          {/* Version detail */}
          <div className="col-span-2">
            {selectedVersionId ? (
              isLoadingDetail ? (
                <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center text-slate-400">
                  Loading...
                </div>
              ) : selectedVersion ? (
                <VersionDetailPanel
                  version={selectedVersion}
                  onRestore={() => handleRestore(selectedVersion)}
                  // onCompare={() => handleCompare(selectedVersion.id)}
                  formatDate={formatDate}
                />
              ) : null
            ) : (
              <div className="bg-slate-800 rounded-xl border border-slate-700 p-8 text-center text-slate-400">
                <Eye className="w-8 h-8 mx-auto mb-2 text-slate-600" />
                Select a version to view details
              </div>
            )}
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      <ConfirmDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={() => deleteConfirm && deleteMutation.mutate(deleteConfirm)}
        title="Delete Version"
        message="Are you sure you want to delete this version? This action cannot be undone."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  )
}

interface VersionCardProps {
  version: VersionItem
  isSelected: boolean
  onView: () => void
  // onCompare: () => void
  onDelete: () => void
  formatDate: (date: string) => string
  truncate: (text: string, length: number) => string
}

function VersionCard({
  version,
  isSelected,
  onView,
  // onCompare,
  onDelete,
  formatDate,
  truncate,
}: VersionCardProps) {
  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer transition-colors ${isSelected
        ? 'border-primary-300 bg-primary-50'
        : 'border-gray-200 bg-white hover:border-gray-300'
        }`}
      onClick={onView}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {version.type === 'adapt' ? (
            <Sparkles className="w-4 h-4 text-primary-600" />
          ) : (
            <FileText className="w-4 h-4 text-green-600" />
          )}
          <span className="text-sm font-medium text-gray-900">
            {version.title || (version.type === 'adapt' ? 'Adapted Resume' : 'Ideal Resume')}
          </span>
        </div>
        <span
          className={`text-xs px-2 py-0.5 rounded ${version.type === 'adapt'
            ? 'bg-primary-100 text-primary-700'
            : 'bg-green-100 text-green-700'
            }`}
        >
          {version.type}
        </span>
      </div>

      <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
        <Calendar className="w-3 h-3" />
        {formatDate(version.created_at)}
      </div>

      {version.result_preview && (
        <p className="text-xs text-gray-500 line-clamp-2">
          {truncate(version.result_preview, 100)}
        </p>
      )}

      <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100">

        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1"
        >
          <Trash2 className="w-3 h-3" />
          Delete
        </button>
      </div>
    </div>
  )
}

interface VersionDetailPanelProps {
  version: VersionDetail
  onRestore: () => void
  // onCompare: () => void
  formatDate: (date: string) => string
}

function VersionDetailPanel({ version, onRestore, formatDate }: VersionDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<'result' | 'resume' | 'vacancy'>('result')

  return (
    <div className="bg-white rounded-xl border border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold text-gray-900">
            {version.title || (version.type === 'adapt' ? 'Adapted Resume' : 'Ideal Resume')}
          </h2>
          <div className="flex items-center gap-2">

            <Button size="sm" onClick={onRestore}>
              <RotateCcw className="w-4 h-4 mr-1" />
              Restore
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            {formatDate(version.created_at)}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-xs ${version.type === 'adapt'
              ? 'bg-primary-100 text-primary-700'
              : 'bg-green-100 text-green-700'
              }`}
          >
            {version.type}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('result')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'result'
            ? 'border-primary-500 text-primary-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
        >
          Result
        </button>
        {version.resume_text && (
          <button
            onClick={() => setActiveTab('resume')}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'resume'
              ? 'border-primary-500 text-primary-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            Original Resume
          </button>
        )}
        <button
          onClick={() => setActiveTab('vacancy')}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === 'vacancy'
            ? 'border-primary-500 text-primary-600'
            : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
        >
          Vacancy
        </button>
      </div>

      {/* Content */}
      <div className="p-4 h-[400px] overflow-auto">
        <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
          {activeTab === 'result' && version.result_text}
          {activeTab === 'resume' && version.resume_text}
          {activeTab === 'vacancy' && version.vacancy_text}
        </pre>
      </div>
    </div>
  )
}

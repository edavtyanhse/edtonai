import { useMemo, useState } from 'react'
import { computeDiff, type DiffGranularity, type DiffSegment } from '@/utils/diff'

interface DiffViewerProps {
  before: string
  after: string
  showOnlyChanges?: boolean
}

export default function DiffViewer({
  before,
  after,
  showOnlyChanges: initialShowOnlyChanges = false,
}: DiffViewerProps) {
  const [granularity, setGranularity] = useState<DiffGranularity>('word')
  const [showOnlyChanges, setShowOnlyChanges] = useState(initialShowOnlyChanges)

  const result = useMemo(
    () => computeDiff(before, after, granularity),
    [before, after, granularity]
  )

  const filteredSegments = useMemo(() => {
    if (!showOnlyChanges) return result.segments

    // When showing only changes, include context around changes
    const segments: DiffSegment[] = []
    const contextSize = 50 // characters of context

    for (let i = 0; i < result.segments.length; i++) {
      const segment = result.segments[i]

      if (segment.type !== 'equal') {
        segments.push(segment)
      } else if (showOnlyChanges) {
        // Check if adjacent to a change
        const prevIsChange = i > 0 && result.segments[i - 1].type !== 'equal'
        const nextIsChange =
          i < result.segments.length - 1 && result.segments[i + 1].type !== 'equal'

        if (prevIsChange || nextIsChange) {
          // Show truncated context
          let text = segment.text
          if (text.length > contextSize * 2) {
            if (prevIsChange && nextIsChange) {
              text = text.slice(0, contextSize) + ' [...] ' + text.slice(-contextSize)
            } else if (prevIsChange) {
              text = text.slice(0, contextSize) + ' [...]'
            } else {
              text = '[...] ' + text.slice(-contextSize)
            }
          }
          segments.push({ ...segment, text })
        } else if (segments.length > 0 && segment.text.trim()) {
          // Add ellipsis between distant changes
          const lastSegment = segments[segments.length - 1]
          if (lastSegment.type !== 'equal' || !lastSegment.text.includes('[...]')) {
            segments.push({ type: 'equal', text: '\n[...]\n' })
          }
        }
      }
    }

    return segments
  }, [result.segments, showOnlyChanges])

  return (
    <div className="flex flex-col h-full">
      {/* Controls */}
      <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Granularity:</span>
            <select
              value={granularity}
              onChange={(e) => setGranularity(e.target.value as DiffGranularity)}
              className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="word">Word</option>
              <option value="line">Line</option>
            </select>
          </div>

          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showOnlyChanges}
              onChange={(e) => setShowOnlyChanges(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            Show only changes
          </label>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-200 border border-green-400" />
            <span className="text-gray-600">+{result.stats.added}</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-200 border border-red-400" />
            <span className="text-gray-600">-{result.stats.removed}</span>
          </span>
        </div>
      </div>

      {/* Diff content */}
      <div className="flex-1 overflow-auto bg-white border border-gray-200 rounded-lg p-4">
        <pre className="font-mono text-sm whitespace-pre-wrap break-words leading-relaxed">
          {filteredSegments.map((segment, index) => (
            <DiffSpan key={index} segment={segment} />
          ))}
        </pre>
      </div>
    </div>
  )
}

function DiffSpan({ segment }: { segment: DiffSegment }) {
  // Use React's built-in text escaping (no dangerouslySetInnerHTML)
  const className = {
    equal: 'diff-equal',
    add: 'diff-added',
    remove: 'diff-removed',
  }[segment.type]

  return <span className={className}>{segment.text}</span>
}

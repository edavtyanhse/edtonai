import { useRef, useEffect, ChangeEvent } from 'react'

interface TextAreaWithCounterProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  label: string
  maxLength: number
  disabled?: boolean
  readOnly?: boolean
  minHeight?: number
}

export default function TextAreaWithCounter({
  value,
  onChange,
  placeholder,
  label,
  maxLength,
  disabled = false,
  readOnly = false,
  minHeight = 200,
}: TextAreaWithCounterProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const charCount = value.length
  const isOverLimit = charCount > maxLength
  const percentage = Math.min((charCount / maxLength) * 100, 100)

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = `${Math.max(textarea.scrollHeight, minHeight)}px`
    }
  }, [value, minHeight])

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-app-text-muted">{label}</label>
        <span
          className={`text-xs ${isOverLimit ? 'text-app-danger font-medium' : 'text-app-text-subtle'}`}
        >
          {charCount.toLocaleString()} / {maxLength.toLocaleString()}
        </span>
      </div>

      <div className="relative flex-1">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readOnly}
          className={`w-full h-full p-3 border rounded-lg text-sm font-mono leading-relaxed transition-colors ${
            isOverLimit
              ? 'border-app-danger/50 focus:border-app-danger focus:ring-app-danger/30 bg-app-surface text-app-text'
              : 'border-app-border focus:border-app-accent focus:ring-app-accent/30 bg-app-surface text-app-text placeholder:text-app-text-subtle'
          } focus:outline-none focus:ring-2 ${
            readOnly ? 'bg-app-surface-muted cursor-default opacity-80' : ''
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
          style={{ minHeight: `${minHeight}px` }}
        />

        {/* Progress indicator */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-app-border rounded-b-lg overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isOverLimit ? 'bg-app-danger' : percentage > 80 ? 'bg-app-warning' : 'bg-app-accent'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {isOverLimit && (
        <p className="mt-1 text-xs text-app-danger">
          Text exceeds maximum length by {(charCount - maxLength).toLocaleString()} characters
        </p>
      )}
    </div>
  )
}

import { useEffect, useState, ReactNode, useCallback } from 'react'
import type {
  ParsedResume,
  ParsedVacancy,
  MatchAnalysis,
  ChangeLogEntry,
} from '@/api'
import { WizardContext, type WizardContextType, initialWizardState } from './WizardContextTypes'

interface WizardState {
  // Step 1 - Resume
  resumeText: string
  resumeId: string | null
  parsedResume: ParsedResume | null

  // Step 2 - Vacancy
  vacancyText: string
  vacancyId: string | null
  parsedVacancy: ParsedVacancy | null

  // Step 3 - Analysis
  analysis: MatchAnalysis | null
  analysisId: string | null
  previousScore: number | null

  // Step 4 - Improvement
  selectedCheckboxes: string[]
  resultText: string
  changeLog: ChangeLogEntry[]
}

const initialState: WizardState = initialWizardState
const STORAGE_KEY = 'wizard_state_v1'

export function WizardProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WizardState>(() => {
    // Try to load from localStorage on init
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const parsed = JSON.parse(saved)
        // Backward compatibility: previously we stored only `state`
        if (parsed && typeof parsed === 'object' && 'state' in parsed) {
          return (parsed as { state: WizardState }).state
        }
        return parsed as WizardState
      }
    } catch (e) {
      console.error('Failed to load wizard state', e)
    }
    return initialState
  })

  const [currentStep, setCurrentStep] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (!saved) return 1
      const parsed = JSON.parse(saved)
      if (parsed && typeof parsed === "object" && "currentStep" in parsed) {
        const step = Number((parsed as { currentStep: unknown }).currentStep)
        return Number.isFinite(step) && step >= 1 && step <= 4 ? step : 1
      }
    } catch {
      // Ignore and fallback to default
    }
    return 1
  })

  // Save to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ state, currentStep }))
    } catch (e) {
      console.error('Failed to save wizard state', e)
    }
  }, [state, currentStep])

  // Step 1 actions
  const setResumeText = useCallback((text: string) => {
    setState((prev) => ({ ...prev, resumeText: text }))
  }, [])

  const setResumeData = useCallback((id: string, parsed: ParsedResume) => {
    setState((prev) => ({
      ...prev,
      resumeId: id,
      parsedResume: parsed,
    }))
  }, [])

  const updateParsedResume = useCallback((parsed: ParsedResume) => {
    setState((prev) => ({ ...prev, parsedResume: parsed }))
  }, [])

  // Step 2 actions
  const setVacancyText = useCallback((text: string) => {
    setState((prev) => ({ ...prev, vacancyText: text }))
  }, [])

  const setVacancyData = useCallback((id: string, parsed: ParsedVacancy) => {
    setState((prev) => ({
      ...prev,
      vacancyId: id,
      parsedVacancy: parsed,
    }))
  }, [])

  const updateParsedVacancy = useCallback((parsed: ParsedVacancy) => {
    setState((prev) => ({ ...prev, parsedVacancy: parsed }))
  }, [])

  // Step 3 actions
  const setAnalysis = useCallback((analysisId: string, analysis: MatchAnalysis) => {
    setState((prev) => ({
      ...prev,
      analysisId,
      // Save previous score for comparison (only if we already had one)
      previousScore: prev.analysis?.score ?? prev.previousScore,
      analysis,
      // Pre-select high-priority checkboxes
      selectedCheckboxes: analysis.checkbox_options
        .filter((o) => o.enabled && (o.priority ?? 0) >= 2)
        .map((o) => o.id),
    }))
  }, [])

  // Step 4 actions
  const setSelectedCheckboxes = useCallback((ids: string[]) => {
    setState((prev) => ({ ...prev, selectedCheckboxes: ids }))
  }, [])

  const toggleCheckbox = useCallback((id: string) => {
    setState((prev) => ({
      ...prev,
      selectedCheckboxes: prev.selectedCheckboxes.includes(id)
        ? prev.selectedCheckboxes.filter((cid) => cid !== id)
        : [...prev.selectedCheckboxes, id],
    }))
  }, [])

  const setResult = useCallback(
    (text: string, changeLog: ChangeLogEntry[]) => {
      setState((prev) => ({
        ...prev,
        resultText: text,
        changeLog,
      }))
    },
    []
  )

  // Apply improved resume as the new base (after user confirms changes)
  const applyImprovedResume = useCallback((newResumeText: string) => {
    setState((prev) => ({
      ...prev,
      resumeText: newResumeText,  // New base resume text
      resultText: '',              // Clear result
      changeLog: [],               // Clear change log
      selectedCheckboxes: [],      // Clear selections
    }))
  }, [])

  // Navigation
  const canGoToStep = useCallback(
    (step: number) => {
      switch (step) {
        case 1:
          return true
        case 2:
          return !!state.parsedResume
        case 3:
          return !!state.parsedResume && !!state.parsedVacancy
        case 4:
          return !!state.analysis
        default:
          return false
      }
    },
    [state.parsedResume, state.parsedVacancy, state.analysis]
  )

  const goToNextStep = useCallback(() => {
    if (currentStep < 4 && canGoToStep(currentStep + 1)) {
      setCurrentStep(currentStep + 1)
    }
  }, [currentStep, canGoToStep])

  const goToPrevStep = useCallback(() => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }, [currentStep])

  // Reset
  const reset = useCallback(() => {
    setState(initialState)
    setCurrentStep(1)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // Ignore storage failures
    }
  }, [])

  const value: WizardContextType = {
    state,
    currentStep,
    setCurrentStep,
    setResumeText,
    setResumeData,
    updateParsedResume,
    setVacancyText,
    setVacancyData,
    updateParsedVacancy,
    setAnalysis,
    setSelectedCheckboxes,
    toggleCheckbox,
    setResult,
    applyImprovedResume,
    canGoToStep,
    goToNextStep,
    goToPrevStep,
    reset,
  }

  return <WizardContext.Provider value={value}>{children}</WizardContext.Provider>
}

export type { WizardContextType }

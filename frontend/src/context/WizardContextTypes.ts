import { createContext } from 'react'
import type {
  ParsedResume,
  ParsedVacancy,
  MatchAnalysis,
  ChangeLogEntry,
} from '@/api'

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
  previousResumeText: string | null
}

export interface WizardContextType {
  state: WizardState
  currentStep: number
  setCurrentStep: (step: number) => void

  // Step 1 actions
  setResumeText: (text: string) => void
  setResumeData: (id: string, parsed: ParsedResume) => void
  updateParsedResume: (parsed: ParsedResume) => void

  // Step 2 actions
  setVacancyText: (text: string) => void
  setVacancyData: (id: string, parsed: ParsedVacancy) => void
  updateParsedVacancy: (parsed: ParsedVacancy) => void

  // Step 3 actions
  setAnalysis: (analysisId: string, analysis: MatchAnalysis) => void

  // Step 4 actions
  setSelectedCheckboxes: (ids: string[]) => void
  toggleCheckbox: (id: string) => void
  setResult: (text: string, changeLog: ChangeLogEntry[]) => void
  applyImprovedResume: (newResumeText: string) => void

  // Navigation
  canGoToStep: (step: number) => boolean
  goToNextStep: () => void
  goToPrevStep: () => void

  // Reset
  reset: () => void
}

export const initialWizardState: WizardState = {
  resumeText: '',
  resumeId: null,
  parsedResume: null,
  vacancyText: '',
  vacancyId: null,
  parsedVacancy: null,
  analysis: null,
  analysisId: null,
  previousScore: null,
  selectedCheckboxes: [],
  resultText: '',
  changeLog: [],
  previousResumeText: null,
}

export const WizardContext = createContext<WizardContextType | null>(null)

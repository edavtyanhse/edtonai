import React from 'react'

export type Language = 'en' | 'ru'

export interface AnalysisResult {
  score: number
  suggestions: string[]
  strengths: string[]
  missingKeywords: string[]
  isLoading: boolean
  error?: string
}

export interface DemoState {
  resumeText: string
  jobDescription: string
}

export interface Feature {
  title: string
  description: string
  icon: React.ElementType
}

export interface Step {
  number: string
  title: string
  description: string
}

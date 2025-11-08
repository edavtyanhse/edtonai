import type { AnalyzeReq, AnalyzeRes, GenerateReq, GenerateRes } from "./api";

const isBrowser = typeof window !== "undefined";

export const ANALYSIS_STORAGE_KEY = "edton.analysis";
export const GENERATION_STORAGE_KEY = "edton.generation";

export type AnalysisSession = {
  request: AnalyzeReq;
  response: AnalyzeRes;
};

export type GenerationSession = {
  request: GenerateReq;
  response: GenerateRes;
};

export function saveAnalysisSession(data: AnalysisSession): void {
  if (!isBrowser) return;
  sessionStorage.setItem(ANALYSIS_STORAGE_KEY, JSON.stringify(data));
}

export function loadAnalysisSession(): AnalysisSession | null {
  if (!isBrowser) return null;
  const raw = sessionStorage.getItem(ANALYSIS_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AnalysisSession;
  } catch (error) {
    console.error("Failed to parse analysis session", error);
    sessionStorage.removeItem(ANALYSIS_STORAGE_KEY);
    return null;
  }
}

export function saveGenerationSession(data: GenerationSession): void {
  if (!isBrowser) return;
  sessionStorage.setItem(GENERATION_STORAGE_KEY, JSON.stringify(data));
}

export function loadGenerationSession(): GenerationSession | null {
  if (!isBrowser) return null;
  const raw = sessionStorage.getItem(GENERATION_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GenerationSession;
  } catch (error) {
    console.error("Failed to parse generation session", error);
    sessionStorage.removeItem(GENERATION_STORAGE_KEY);
    return null;
  }
}

export function clearGenerationSession(): void {
  if (!isBrowser) return;
  sessionStorage.removeItem(GENERATION_STORAGE_KEY);
}

